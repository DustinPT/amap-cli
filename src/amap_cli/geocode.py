"""Shared geocoding helpers for CLI commands."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from amap_cli.api import AmapApiClient
from amap_cli.errors import ApiResponseError
from amap_cli.params import Coordinate, parse_coordinate


@dataclass(frozen=True, slots=True)
class GeocodeResult:
    """Normalized geocoding result for CLI commands."""

    coordinate: Coordinate
    formatted_address: str | None


def geocode_text(
    value: str,
    *,
    client: AmapApiClient,
    city: str | None = None,
) -> GeocodeResult:
    """Convert a place name to a coordinate with the geocoding API."""
    params: dict[str, Any] = {"address": value}
    if city is not None:
        params["city"] = city

    payload = client.get("/v3/geocode/geo", params=params)
    geocodes = payload.get("geocodes")
    if not isinstance(geocodes, list) or not geocodes:
        raise ApiResponseError(
            f"未找到地点：{value}",
            details={"address": value, "city": city},
        )

    first = geocodes[0]
    if not isinstance(first, dict):
        raise ApiResponseError(
            "地理编码响应格式无效。",
            details={"address": value, "city": city},
        )

    location_value = first.get("location")
    if not isinstance(location_value, str) or not location_value.strip():
        raise ApiResponseError(
            "地理编码结果缺少坐标信息。",
            details={"address": value, "city": city},
        )

    formatted_address = first.get("formatted_address")
    if not isinstance(formatted_address, str) or not formatted_address.strip():
        formatted_address = None

    return GeocodeResult(
        coordinate=parse_coordinate(location_value, "geocode.location"),
        formatted_address=formatted_address,
    )
