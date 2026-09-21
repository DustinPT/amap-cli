"""Geocode command registration and handlers."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Any

from amap_cli.api import AmapApiClient
from amap_cli.geocode import GeocodeResult, geocode_text
from amap_cli.params import normalize_text_argument


@dataclass(frozen=True, slots=True)
class GeocodeRequest:
    """Validated geocode command input."""

    address: str
    city: str | None

    @classmethod
    def from_args(cls, args: argparse.Namespace) -> "GeocodeRequest":
        """Build a validated geocode request from parsed CLI arguments."""
        return cls(
            address=normalize_text_argument(args.address, "address"),
            city=(
                normalize_text_argument(args.city, "city")
                if args.city is not None
                else None
            ),
        )

    def build_state(self) -> dict[str, Any]:
        """Build CLI-facing state metadata."""
        state: dict[str, Any] = {"address": self.address}
        if self.city is not None:
            state["city"] = self.city
        return state


def register_geocode_command(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> argparse.ArgumentParser:
    """Register the `geocode` command on a subparser collection."""
    parser = subparsers.add_parser(
        "geocode",
        help="将地点名称解析为坐标",
        description="调用高德地理编码接口，将结构化地址或地标名称解析为坐标。",
    )
    parser.add_argument(
        "--address",
        required=True,
        help="待解析的结构化地址或地标名称",
    )
    parser.add_argument(
        "--city",
        help="可选城市，用于缩小地理编码范围",
    )
    parser.set_defaults(handler=handle_geocode_command)
    return parser


def handle_geocode_command(
    args: argparse.Namespace,
    *,
    client: AmapApiClient | None = None,
) -> dict[str, Any]:
    """Handle the `geocode` command and normalize the response."""
    request = GeocodeRequest.from_args(args)
    result = geocode_text(
        request.address,
        client=client or AmapApiClient(),
        city=request.city,
    )
    return {
        "state": request.build_state(),
        "geocode": _normalize_geocode_result(result),
    }


def _normalize_geocode_result(result: GeocodeResult) -> dict[str, Any]:
    """Normalize the geocode result to the CLI output shape."""
    payload: dict[str, Any] = {
        "location": [
            round(result.coordinate.longitude, 6),
            round(result.coordinate.latitude, 6),
        ]
    }
    if result.formatted_address is not None:
        payload["formattedAddress"] = result.formatted_address
    return payload
