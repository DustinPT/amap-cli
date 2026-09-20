"""Route command argument registration and route planning handlers."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any

from amap_cli.api import AmapApiClient
from amap_cli.errors import ApiResponseError, ValidationError
from amap_cli.geocode import geocode_text
from amap_cli.params import Coordinate, LocationInput, normalize_text_argument, parse_location_input

ROUTE_TYPES = ("driving", "walking", "riding", "transit")
DRIVING_POLICIES = ("fastest", "least_fee", "shortest", "no_highway", "avoid_jam")
TRANSIT_STRATEGIES = (
    "fastest",
    "least_cost",
    "least_walk",
    "most_comfort",
    "no_subway",
)
DRIVING_POLICY_TO_STRATEGY = {
    "fastest": "0",
    "least_fee": "1",
    "shortest": "2",
    "no_highway": "3",
    "avoid_jam": "4",
}
TRANSIT_STRATEGY_TO_POLICY = {
    "fastest": "0",
    "least_cost": "1",
    "least_walk": "3",
    "most_comfort": "4",
    "no_subway": "5",
}
MAX_WAYPOINTS = 16


@dataclass(frozen=True, slots=True)
class PreparedRouteRequest:
    """Validated route command arguments before geocoding."""

    origin: LocationInput
    origin_name: str | None
    destination: LocationInput
    destination_name: str | None
    route_type: str
    waypoints: list[LocationInput]
    policy: str | None
    strategy: str | None
    city: str | None


@dataclass(frozen=True, slots=True)
class ResolvedRoutePoint:
    """Route point after converting names to coordinates when needed."""

    raw: str
    name: str
    coordinate: Coordinate
    formatted_address: str | None = None

    def to_state(self) -> dict[str, Any]:
        """Convert the point to the CLI state shape."""
        state: dict[str, Any] = {
            "name": self.name,
            "position": [
                round(self.coordinate.longitude, 6),
                round(self.coordinate.latitude, 6),
            ],
        }
        if self.formatted_address is not None:
            state["formattedAddress"] = self.formatted_address
        return state


def register_route_command(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register the `route` command and its arguments."""
    parser = subparsers.add_parser("route", help="执行路径规划")
    parser.add_argument(
        "--from",
        dest="origin",
        required=True,
        help="起点，支持地名或 `经度,纬度`",
    )
    parser.add_argument(
        "--from-name",
        dest="origin_name",
        help="起点显示名称，通常配合坐标使用",
    )
    parser.add_argument(
        "--to",
        dest="destination",
        required=True,
        help="终点，支持地名或 `经度,纬度`",
    )
    parser.add_argument(
        "--to-name",
        dest="destination_name",
        help="终点显示名称，通常配合坐标使用",
    )
    parser.add_argument(
        "--type",
        dest="route_type",
        required=True,
        choices=ROUTE_TYPES,
        help="路径类型",
    )
    parser.add_argument(
        "--waypoints",
        help="加号分隔的途经点，仅支持 driving，例如 `A+B` 或 `116.1,39.9+中关村`",
    )
    parser.add_argument(
        "--policy",
        choices=DRIVING_POLICIES,
        help="驾车策略，仅支持 driving",
    )
    parser.add_argument(
        "--strategy",
        choices=TRANSIT_STRATEGIES,
        help="公交策略，仅支持 transit",
    )
    parser.add_argument("--city", help="公交路线规划的城市名")
    parser.set_defaults(handler=handle_route_command)


def handle_route_command(
    args: argparse.Namespace,
    *,
    client: AmapApiClient | None = None,
) -> dict[str, Any]:
    """Handle the `route` command and return normalized JSON data."""
    prepared = _prepare_route_request(args)
    api_client = client or AmapApiClient()

    geocode_city = prepared.city if prepared.route_type == "transit" else None
    origin = _resolve_route_point(
        prepared.origin,
        display_name=prepared.origin_name,
        client=api_client,
        city=geocode_city,
    )
    destination = _resolve_route_point(
        prepared.destination,
        display_name=prepared.destination_name,
        client=api_client,
        city=geocode_city,
    )
    waypoints = [
        _resolve_route_point(waypoint, display_name=None, client=api_client, city=None)
        for waypoint in prepared.waypoints
    ]

    payload = _request_route_payload(
        api_client,
        route_type=prepared.route_type,
        origin=origin,
        destination=destination,
        waypoints=waypoints,
        policy=prepared.policy,
        strategy=prepared.strategy,
        city=prepared.city,
    )

    return {
        "state": _build_route_state(
            origin=origin,
            destination=destination,
            waypoints=waypoints,
            route_type=prepared.route_type,
            policy=prepared.policy,
            strategy=prepared.strategy,
            city=prepared.city,
        ),
        "summary": _build_route_summary(prepared.route_type, payload),
    }


def _prepare_route_request(args: argparse.Namespace) -> PreparedRouteRequest:
    """Validate command arguments and normalize the request model."""
    origin = parse_location_input(args.origin, "from")
    destination = parse_location_input(args.destination, "to")
    route_type = normalize_text_argument(args.route_type, "type")
    origin_name = _normalize_optional_text(args.origin_name, "from-name")
    destination_name = _normalize_optional_text(args.destination_name, "to-name")
    policy = _normalize_optional_text(args.policy, "policy")
    strategy = _normalize_optional_text(args.strategy, "strategy")
    city = _normalize_optional_text(args.city, "city")
    waypoints = _parse_waypoints(args.waypoints)

    if route_type != "driving" and waypoints:
        raise ValidationError("`--waypoints` 仅支持 `--type driving`。")
    if route_type != "driving" and policy is not None:
        raise ValidationError("`--policy` 仅支持 `--type driving`。")
    if route_type != "transit" and strategy is not None:
        raise ValidationError("`--strategy` 仅支持 `--type transit`。")
    if route_type == "transit" and city is None:
        raise ValidationError("`--type transit` 时必须提供 `--city`。")
    if route_type != "transit" and city is not None:
        raise ValidationError("`--city` 仅支持 `--type transit`。")

    return PreparedRouteRequest(
        origin=origin,
        origin_name=origin_name,
        destination=destination,
        destination_name=destination_name,
        route_type=route_type,
        waypoints=waypoints,
        policy=policy,
        strategy=strategy,
        city=city,
    )


def _normalize_optional_text(value: str | None, field_name: str) -> str | None:
    """Trim an optional text argument when present."""
    if value is None:
        return None
    return normalize_text_argument(value, field_name)


def _parse_waypoints(value: str | None) -> list[LocationInput]:
    """Parse `--waypoints` into validated route points."""
    if value is None:
        return []

    normalized = normalize_text_argument(value, "waypoints")
    items = [item.strip() for item in normalized.split("+")]
    if any(not item for item in items):
        raise ValidationError(
            "`--waypoints` 必须使用加号分隔非空途经点，例如 `A+B`。"
        )
    if len(items) > MAX_WAYPOINTS:
        raise ValidationError(f"`--waypoints` 最多支持 {MAX_WAYPOINTS} 个途经点。")

    return [
        parse_location_input(item, f"waypoints[{index}]")
        for index, item in enumerate(items, start=1)
    ]


def _resolve_route_point(
    location: LocationInput,
    *,
    display_name: str | None,
    client: AmapApiClient,
    city: str | None,
) -> ResolvedRoutePoint:
    """Resolve a route point to a display name and coordinate."""
    if location.coordinate is not None:
        return ResolvedRoutePoint(
            raw=location.raw,
            name=display_name or location.raw,
            coordinate=location.coordinate,
        )

    geocoded = geocode_text(location.name or location.raw, client=client, city=city)
    return ResolvedRoutePoint(
        raw=location.raw,
        name=display_name or location.name or location.raw,
        coordinate=geocoded.coordinate,
        formatted_address=geocoded.formatted_address,
    )


def _request_route_payload(
    client: AmapApiClient,
    *,
    route_type: str,
    origin: ResolvedRoutePoint,
    destination: ResolvedRoutePoint,
    waypoints: list[ResolvedRoutePoint],
    policy: str | None,
    strategy: str | None,
    city: str | None,
) -> dict[str, Any]:
    """Call the corresponding Amap route API for the requested mode."""
    if route_type == "driving":
        params: dict[str, Any] = {
            "origin": origin.coordinate.to_amap_value(),
            "destination": destination.coordinate.to_amap_value(),
            "extensions": "all",
        }
        if waypoints:
            params["waypoints"] = ";".join(
                waypoint.coordinate.to_amap_value() for waypoint in waypoints
            )
        if policy is not None:
            params["strategy"] = DRIVING_POLICY_TO_STRATEGY[policy]
        return client.get("/v3/direction/driving", params=params)

    if route_type == "walking":
        return client.get(
            "/v3/direction/walking",
            params={
                "origin": origin.coordinate.to_amap_value(),
                "destination": destination.coordinate.to_amap_value(),
            },
        )

    if route_type == "riding":
        payload = client.get(
            "/v4/direction/bicycling",
            params={
                "origin": origin.coordinate.to_amap_value(),
                "destination": destination.coordinate.to_amap_value(),
            },
        )
        _raise_for_bicycling_error(payload)
        return payload

    return client.get(
        "/v3/direction/transit/integrated",
        params={
            "origin": origin.coordinate.to_amap_value(),
            "destination": destination.coordinate.to_amap_value(),
            "city": city,
            "extensions": "all",
            **(
                {"strategy": TRANSIT_STRATEGY_TO_POLICY[strategy]}
                if strategy is not None
                else {}
            ),
        },
    )


def _raise_for_bicycling_error(payload: dict[str, Any]) -> None:
    """Normalize bicycling API errors which use `errcode` instead of `status`."""
    errcode = payload.get("errcode")
    if errcode in (None, 0, "0"):
        return

    raise ApiResponseError(
        payload.get("errmsg") or "高德骑行路径规划失败。",
        details={
            "errcode": errcode,
            "errdetail": payload.get("errdetail"),
        },
    )


def _build_route_state(
    *,
    origin: ResolvedRoutePoint,
    destination: ResolvedRoutePoint,
    waypoints: list[ResolvedRoutePoint],
    route_type: str,
    policy: str | None,
    strategy: str | None,
    city: str | None,
) -> dict[str, Any]:
    """Build the normalized route state payload."""
    state = {
        "from": origin.to_state(),
        "to": destination.to_state(),
        "waypoints": [waypoint.to_state() for waypoint in waypoints],
        "type": route_type,
    }
    if policy is not None:
        state["policy"] = policy
    if strategy is not None:
        state["strategy"] = strategy
    if city is not None:
        state["city"] = city
    return state


def _build_route_summary(route_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Convert raw Amap route results to a CLI-friendly summary."""
    if route_type == "driving":
        return _build_path_summary(_extract_route_path(payload, "driving"), include_tolls=True)
    if route_type == "walking":
        return _build_path_summary(_extract_route_path(payload, "walking"), include_tolls=False)
    if route_type == "riding":
        return _build_path_summary(_extract_bicycling_path(payload), include_tolls=False)
    return _build_transit_summary(payload)


def _extract_route_path(payload: dict[str, Any], route_type: str) -> dict[str, Any]:
    """Extract the first path from v3 direction APIs."""
    route = payload.get("route")
    if not isinstance(route, dict):
        raise ApiResponseError(f"{route_type} 路径规划返回缺少 `route`。")

    paths = route.get("paths")
    if not isinstance(paths, list) or not paths:
        raise ApiResponseError(f"{route_type} 路径规划未返回可用路线。")

    first = paths[0]
    if not isinstance(first, dict):
        raise ApiResponseError(f"{route_type} 路径规划返回的路径格式无效。")
    return first


def _extract_bicycling_path(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract the first path from the bicycling API payload."""
    data = payload.get("data", payload)
    if not isinstance(data, dict):
        raise ApiResponseError("骑行路径规划返回格式无效。")

    paths = data.get("paths")
    if not isinstance(paths, list) or not paths:
        raise ApiResponseError("骑行路径规划未返回可用路线。")

    first = paths[0]
    if not isinstance(first, dict):
        raise ApiResponseError("骑行路径规划返回的路径格式无效。")
    return first


def _build_path_summary(path: dict[str, Any], *, include_tolls: bool) -> dict[str, Any]:
    """Build a summary for driving, walking, or riding path responses."""
    summary = {
        "distance": _parse_int(path.get("distance")),
        "time": _parse_int(path.get("duration")),
        "steps": [_build_step_summary(step) for step in _iter_dict_list(path.get("steps"))],
    }

    if include_tolls:
        summary["tolls"] = _parse_float(path.get("tolls"))

    return summary


def _build_step_summary(step: dict[str, Any]) -> dict[str, Any]:
    """Build the normalized step payload for path-based modes."""
    return {
        "instruction": _string_value(step.get("instruction")),
        "road": _string_value(step.get("road")),
        "distance": _parse_int(step.get("distance")),
        "time": _parse_int(step.get("duration")),
        "action": _string_value(step.get("action")),
    }


def _build_transit_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Build the summary payload for transit route results."""
    route = payload.get("route")
    if not isinstance(route, dict):
        raise ApiResponseError("公交路径规划返回缺少 `route`。")

    transits = route.get("transits")
    if not isinstance(transits, list) or not transits:
        raise ApiResponseError("公交路径规划未返回可用路线。")

    transit = transits[0]
    if not isinstance(transit, dict):
        raise ApiResponseError("公交路径规划返回的线路格式无效。")

    return {
        "distance": _parse_int(transit.get("distance")),
        "time": _parse_int(transit.get("duration")),
        "cost": _parse_float(transit.get("cost")),
        "walking_distance": _parse_int(transit.get("walking_distance")),
        "nightflag": _string_value(transit.get("nightflag")) == "1",
        "steps": _build_transit_steps(transit),
    }


def _build_transit_steps(transit: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten transit segments into CLI-friendly steps."""
    steps: list[dict[str, Any]] = []
    for segment in _iter_dict_list(transit.get("segments")):
        walking = segment.get("walking")
        if isinstance(walking, dict):
            steps.extend(_build_transit_walking_steps(walking))

        bus = segment.get("bus")
        if isinstance(bus, dict):
            steps.extend(_build_transit_bus_steps(bus))

        railway = segment.get("railway")
        if isinstance(railway, dict) and railway:
            railway_step = _build_transit_railway_step(railway)
            if railway_step is not None:
                steps.append(railway_step)

        taxi = segment.get("taxi")
        if isinstance(taxi, dict) and taxi:
            taxi_step = _build_transit_taxi_step(taxi)
            if taxi_step is not None:
                steps.append(taxi_step)

    return steps


def _build_transit_walking_steps(walking: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert a transit walking segment into individual steps."""
    raw_steps = _iter_dict_list(walking.get("steps"))
    if raw_steps:
        return [
            {
                "type": "walking",
                "instruction": _string_value(step.get("instruction")),
                "road": _string_value(step.get("road")),
                "distance": _parse_int(step.get("distance")),
                "time": _parse_int(step.get("duration")),
                "action": _string_value(step.get("action")),
            }
            for step in raw_steps
        ]

    return [
        {
            "type": "walking",
            "instruction": "步行",
            "road": "",
            "distance": _parse_int(walking.get("distance")),
            "time": _parse_int(walking.get("duration")),
            "action": "",
        }
    ]


def _build_transit_bus_steps(bus: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert transit bus sub-segments into CLI-friendly steps."""
    steps: list[dict[str, Any]] = []

    for line in _iter_dict_list(bus.get("buslines")):
        bus_name = _string_value(line.get("name"))
        departure_stop = _extract_stop_name(line.get("departure_stop"))
        arrival_stop = _extract_stop_name(line.get("arrival_stop"))
        via_num = _parse_int(line.get("via_num"))

        instruction = f"乘坐 {bus_name}".strip()
        if departure_stop or arrival_stop:
            instruction = (
                f"{instruction}，从 {departure_stop or '上车站'} 到 {arrival_stop or '下车站'}"
            )

        steps.append(
            {
                "type": "bus",
                "instruction": instruction,
                "line": bus_name,
                "distance": _parse_int(line.get("distance")),
                "time": _parse_int(line.get("duration")),
                "departure_stop": departure_stop,
                "arrival_stop": arrival_stop,
                "via_num": via_num,
            }
        )

    return steps


def _build_transit_railway_step(railway: dict[str, Any]) -> dict[str, Any] | None:
    """Convert a railway transit segment to a step."""
    name = _string_value(railway.get("name"))
    trip = _string_value(railway.get("trip"))
    instruction = f"乘坐 {trip or name}".strip()
    if not instruction:
        return None

    return {
        "type": "railway",
        "instruction": instruction,
        "line": trip or name,
        "distance": _parse_int(railway.get("distance")),
        "time": _parse_int(railway.get("time")),
        "departure_stop": _extract_stop_name(railway.get("departure_stop")),
        "arrival_stop": _extract_stop_name(railway.get("arrival_stop")),
    }


def _build_transit_taxi_step(taxi: dict[str, Any]) -> dict[str, Any] | None:
    """Convert a taxi transit segment to a step."""
    distance = _parse_int(taxi.get("distance"))
    duration = _parse_int(taxi.get("duration"))
    cost = _parse_float(taxi.get("cost"))
    if distance is None and duration is None and cost is None:
        return None

    return {
        "type": "taxi",
        "instruction": "打车前往",
        "distance": distance,
        "time": duration,
        "cost": cost,
    }


def _extract_stop_name(value: Any) -> str:
    """Extract a stop name from a nested stop object."""
    if not isinstance(value, dict):
        return ""
    return _string_value(value.get("name"))


def _iter_dict_list(value: Any) -> list[dict[str, Any]]:
    """Return only dictionary items from a list-like payload field."""
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _parse_int(value: Any) -> int | None:
    """Parse an integer-like response field."""
    if value in (None, ""):
        return None
    try:
        return int(float(str(value)))
    except (TypeError, ValueError):
        return None


def _parse_float(value: Any) -> float | None:
    """Parse a float-like response field."""
    if value in (None, ""):
        return None
    try:
        return float(str(value))
    except (TypeError, ValueError):
        return None


def _string_value(value: Any) -> str:
    """Convert a response field to a stripped string."""
    if value is None:
        return ""
    return str(value).strip()
