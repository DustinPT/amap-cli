"""Straight-line distance command registration and handlers."""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass
from typing import Callable

from amap_cli.api import AmapApiClient
from amap_cli.geocode import geocode_text
from amap_cli.params import (
    Coordinate,
    LocationInput,
    normalize_text_argument,
    parse_location_input,
)

EARTH_RADIUS_METERS = 6_371_008.8


@dataclass(frozen=True, slots=True)
class PreparedDistanceRequest:
    """Validated distance command arguments before geocoding."""

    origin: LocationInput
    origin_name: str | None
    destination: LocationInput
    destination_name: str | None


@dataclass(frozen=True, slots=True)
class ResolvedDistancePoint:
    """Distance point after resolving names to coordinates when needed."""

    raw: str
    name: str
    coordinate: Coordinate
    formatted_address: str | None = None

    def to_state(self) -> dict[str, object]:
        """Convert the point to the CLI state shape."""
        state: dict[str, object] = {
            "name": self.name,
            "position": [
                round(self.coordinate.longitude, 6),
                round(self.coordinate.latitude, 6),
            ],
        }
        if self.formatted_address is not None:
            state["formattedAddress"] = self.formatted_address
        return state


def register_distance_command(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Register the `distance` command on a subparser collection."""
    parser = subparsers.add_parser(
        "distance",
        help="计算两个地点之间的直线距离",
        description="计算两个地点之间的直线距离；坐标直接本地计算，地名会先做地理编码。",
    )
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
    parser.set_defaults(handler=handle_distance_command)
    return parser


def handle_distance_command(
    args: argparse.Namespace,
    *,
    client: AmapApiClient | None = None,
) -> dict[str, object]:
    """Handle the `distance` command and return normalized JSON data."""
    request = _prepare_distance_request(args)
    client_holder: list[AmapApiClient | None] = [client]

    def get_client() -> AmapApiClient:
        if client_holder[0] is None:
            client_holder[0] = AmapApiClient()
        return client_holder[0]

    origin = _resolve_distance_point(
        request.origin,
        display_name=request.origin_name,
        client_factory=get_client,
    )

    destination = _resolve_distance_point(
        request.destination,
        display_name=request.destination_name,
        client_factory=get_client,
    )

    distance_meters = _calculate_straight_line_distance(
        origin.coordinate,
        destination.coordinate,
    )

    return {
        "state": {
            "from": origin.to_state(),
            "to": destination.to_state(),
            "mode": "straight_line",
            "unit": "meter",
            "source": "local_haversine",
        },
        "summary": {
            "distance": distance_meters,
            "distanceKilometers": round(distance_meters / 1000, 3),
        },
    }


def _prepare_distance_request(args: argparse.Namespace) -> PreparedDistanceRequest:
    """Validate and normalize distance command arguments."""
    return PreparedDistanceRequest(
        origin=parse_location_input(args.origin, "from"),
        origin_name=_normalize_optional_text(args.origin_name, "from-name"),
        destination=parse_location_input(args.destination, "to"),
        destination_name=_normalize_optional_text(args.destination_name, "to-name"),
    )


def _normalize_optional_text(value: str | None, field_name: str) -> str | None:
    """Trim an optional text argument when present."""
    if value is None:
        return None
    return normalize_text_argument(value, field_name)


def _resolve_distance_point(
    location: LocationInput,
    *,
    display_name: str | None,
    client_factory: Callable[[], AmapApiClient],
) -> ResolvedDistancePoint:
    """Resolve a distance point to a display name and coordinate."""
    if location.coordinate is not None:
        return ResolvedDistancePoint(
            raw=location.raw,
            name=display_name or location.raw,
            coordinate=location.coordinate,
        )

    client = client_factory()
    geocoded = geocode_text(location.name or location.raw, client=client)
    return ResolvedDistancePoint(
        raw=location.raw,
        name=display_name or location.name or location.raw,
        coordinate=geocoded.coordinate,
        formatted_address=geocoded.formatted_address,
    )


def _calculate_straight_line_distance(origin: Coordinate, destination: Coordinate) -> int:
    """Calculate the great-circle distance in meters with the Haversine formula."""
    origin_lat = math.radians(origin.latitude)
    origin_lng = math.radians(origin.longitude)
    destination_lat = math.radians(destination.latitude)
    destination_lng = math.radians(destination.longitude)

    delta_lat = destination_lat - origin_lat
    delta_lng = destination_lng - origin_lng

    haversine = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(origin_lat)
        * math.cos(destination_lat)
        * math.sin(delta_lng / 2) ** 2
    )
    central_angle = 2 * math.atan2(math.sqrt(haversine), math.sqrt(1 - haversine))
    return round(EARTH_RADIUS_METERS * central_angle)
