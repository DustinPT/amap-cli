"""POI search command registration and handlers."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any

from amap_cli.api import AmapApiClient
from amap_cli.errors import ValidationError
from amap_cli.params import Coordinate, normalize_text_argument, parse_coordinate

DEFAULT_RADIUS = 3000
DEFAULT_PAGE_SIZE = 10
DEFAULT_PAGE_INDEX = 1
MAX_PAGE_SIZE = 25
MAX_RADIUS = 50000
TEXT_SEARCH_PATH = "/v3/place/text"
AROUND_SEARCH_PATH = "/v3/place/around"


@dataclass(frozen=True, slots=True)
class SearchPoiRequest:
    """Normalized search-poi command input."""

    keyword: str
    city: str | None
    center: Coordinate | None
    radius: int
    page_size: int
    page_index: int

    @property
    def is_nearby_search(self) -> bool:
        """Return whether the request should use nearby search."""
        return self.center is not None

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "SearchPoiRequest":
        """Build a validated request from parsed CLI arguments."""
        keyword = normalize_text_argument(args.keyword, "keyword")
        city = (
            normalize_text_argument(args.city, "city")
            if args.city is not None
            else None
        )
        center = (
            parse_coordinate(args.center, "center")
            if args.center is not None
            else None
        )

        radius = _validate_positive_int(
            args.radius,
            "radius",
            min_value=1,
            max_value=MAX_RADIUS,
        )
        page_size = _validate_positive_int(
            args.pageSize,
            "pageSize",
            min_value=1,
            max_value=MAX_PAGE_SIZE,
        )
        page_index = _validate_positive_int(
            args.pageIndex,
            "pageIndex",
            min_value=1,
        )

        if center is None and getattr(args, "radius", None) != DEFAULT_RADIUS:
            raise ValidationError("仅在提供 `--center` 时允许传入 `--radius`。")

        return cls(
            keyword=keyword,
            city=city,
            center=center,
            radius=radius,
            page_size=page_size,
            page_index=page_index,
        )

    def to_api_request(self) -> tuple[str, dict[str, Any]]:
        """Convert the normalized request to Amap REST API arguments."""
        params: dict[str, Any] = {
            "keywords": self.keyword,
            "offset": self.page_size,
            "page": self.page_index,
            "extensions": "all",
        }

        if self.is_nearby_search:
            params["location"] = self.center.to_amap_value() if self.center else None
            params["radius"] = self.radius
            return AROUND_SEARCH_PATH, params

        if self.city is not None:
            params["city"] = self.city
        return TEXT_SEARCH_PATH, params

    def build_state(self, total: int) -> dict[str, Any]:
        """Build CLI-facing state metadata."""
        state: dict[str, Any] = {
            "keyword": self.keyword,
            "pageSize": self.page_size,
            "pageIndex": self.page_index,
            "extensions": "all",
            "resultCount": total,
        }

        if self.is_nearby_search:
            state["center"] = (
                [self.center.longitude, self.center.latitude]
                if self.center is not None
                else None
            )
            state["radius"] = self.radius
        elif self.city is not None:
            state["city"] = self.city

        return state


def register_search_poi_command(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Register the `search-poi` command on a subparser collection."""
    parser = subparsers.add_parser(
        "search-poi",
        help="搜索 POI",
        description="按关键词或周边范围搜索 POI。",
    )
    add_search_poi_arguments(parser)
    parser.set_defaults(handler=handle_search_poi)
    return parser


def add_search_poi_arguments(parser: argparse.ArgumentParser) -> None:
    """Add search-poi arguments to a parser."""
    parser.add_argument("--keyword", required=True, help="搜索关键词")
    parser.add_argument("--city", help="搜索城市")
    parser.add_argument("--center", help="周边搜索中心，格式为 `经度,纬度`")
    parser.add_argument(
        "--radius",
        type=int,
        default=DEFAULT_RADIUS,
        help=f"周边搜索半径（米），默认 {DEFAULT_RADIUS}",
    )
    parser.add_argument(
        "--pageSize",
        type=int,
        default=DEFAULT_PAGE_SIZE,
        help=f"每页数量，范围 1-{MAX_PAGE_SIZE}，默认 {DEFAULT_PAGE_SIZE}",
    )
    parser.add_argument(
        "--pageIndex",
        type=int,
        default=DEFAULT_PAGE_INDEX,
        help=f"页码，从 1 开始，默认 {DEFAULT_PAGE_INDEX}",
    )


def handle_search_poi(
    args: argparse.Namespace,
    *,
    client: AmapApiClient | None = None,
) -> dict[str, Any]:
    """Handle the `search-poi` command and normalize the response."""
    request = SearchPoiRequest.from_args(args)
    api_client = client or AmapApiClient()
    path, params = request.to_api_request()
    payload = api_client.get(path, params=params)

    total = _parse_total(payload.get("count"))
    return {
        "state": request.build_state(total),
        "pois": _normalize_pois(payload.get("pois")),
        "total": total,
        "pageIndex": request.page_index,
        "pageSize": request.page_size,
    }


def _validate_positive_int(
    value: Any,
    field_name: str,
    *,
    min_value: int,
    max_value: int | None = None,
) -> int:
    """Validate a positive integer CLI argument."""
    if not isinstance(value, int):
        raise ValidationError(f"`{field_name}` 必须是整数。")
    if value < min_value:
        raise ValidationError(f"`{field_name}` 必须大于等于 {min_value}。")
    if max_value is not None and value > max_value:
        raise ValidationError(f"`{field_name}` 必须小于等于 {max_value}。")
    return value


def _parse_total(value: Any) -> int:
    """Convert the Amap `count` field to an integer."""
    if value in (None, ""):
        return 0
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _normalize_pois(value: Any) -> list[dict[str, Any]]:
    """Normalize the raw Amap POI list to the CLI output shape."""
    if not isinstance(value, list):
        return []

    return [_normalize_poi(item) for item in value if isinstance(item, dict)]


def _normalize_poi(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize a single POI payload."""
    return {
        "id": _normalize_optional_text(raw.get("id")),
        "name": _normalize_optional_text(raw.get("name")),
        "type": _normalize_optional_text(raw.get("type")),
        "location": _parse_location(raw.get("location")),
        "address": _normalize_optional_text(raw.get("address")),
        "distance": _parse_distance(raw.get("distance")),
        "tel": _normalize_optional_text(raw.get("tel")),
        "pname": _normalize_optional_text(raw.get("pname")),
        "cityname": _normalize_optional_text(raw.get("cityname")),
        "adname": _normalize_optional_text(raw.get("adname")),
        "photo": _extract_photo(raw.get("photos")),
    }


def _parse_location(value: Any) -> list[float] | None:
    """Parse API location strings into `[lng, lat]` lists."""
    if not isinstance(value, str) or not value.strip():
        return None

    parts = [part.strip() for part in value.split(",", 1)]
    if len(parts) != 2:
        return None

    try:
        return [float(parts[0]), float(parts[1])]
    except ValueError:
        return None


def _parse_distance(value: Any) -> int | None:
    """Convert the API distance field to an integer when available."""
    if value in (None, ""):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _extract_photo(value: Any) -> str | None:
    """Extract the first photo URL from the Amap photo list."""
    if not isinstance(value, list):
        return None

    for item in value:
        if not isinstance(item, dict):
            continue
        url = _normalize_optional_text(item.get("url"))
        if url is not None:
            return url

    return None


def _normalize_optional_text(value: Any) -> str | None:
    """Trim optional text fields and normalize empty strings to None."""
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None
