"""Shared argument parsing helpers for future business commands."""

from __future__ import annotations

import re
from dataclasses import dataclass

from amap_cli.errors import ValidationError

COORDINATE_PATTERN = re.compile(
    r"^\s*([-+]?\d+(?:\.\d+)?)\s*,\s*([-+]?\d+(?:\.\d+)?)\s*$"
)


@dataclass(frozen=True, slots=True)
class Coordinate:
    """A validated longitude/latitude pair."""

    longitude: float
    latitude: float

    def to_amap_value(self) -> str:
        """Convert to the `lng,lat` format expected by Amap APIs."""
        return f"{self.longitude:.6f},{self.latitude:.6f}"


@dataclass(frozen=True, slots=True)
class LocationInput:
    """A location argument that may be coordinates or a place name."""

    raw: str
    kind: str
    coordinate: Coordinate | None = None
    name: str | None = None


def normalize_text_argument(value: str, field_name: str) -> str:
    """Trim and validate a text argument."""
    normalized = value.strip()
    if not normalized:
        raise ValidationError(f"`{field_name}` 不能为空。")
    return normalized


def parse_coordinate(value: str, field_name: str = "location") -> Coordinate:
    """Parse a `lng,lat` string into a validated coordinate object."""
    normalized = normalize_text_argument(value, field_name)
    matched = COORDINATE_PATTERN.match(normalized)
    if matched is None:
        raise ValidationError(
            f"`{field_name}` 必须是 `经度,纬度` 格式，例如 `116.397,39.909`。"
        )

    longitude = float(matched.group(1))
    latitude = float(matched.group(2))

    if not -180 <= longitude <= 180:
        raise ValidationError(f"`{field_name}` 中的经度超出范围 [-180, 180]。")
    if not -90 <= latitude <= 90:
        raise ValidationError(f"`{field_name}` 中的纬度超出范围 [-90, 90]。")

    return Coordinate(longitude=longitude, latitude=latitude)


def parse_location_input(value: str, field_name: str) -> LocationInput:
    """Parse a future route/search location argument."""
    normalized = normalize_text_argument(value, field_name)

    if COORDINATE_PATTERN.match(normalized):
        coordinate = parse_coordinate(normalized, field_name)
        return LocationInput(
            raw=normalized,
            kind="coordinate",
            coordinate=coordinate,
        )

    return LocationInput(raw=normalized, kind="text", name=normalized)
