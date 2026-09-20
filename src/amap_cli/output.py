"""Helpers for unified JSON output."""

from __future__ import annotations

import json
import sys
from typing import Any, TextIO

from amap_cli.errors import AmapCliError


def build_success_payload(data: Any) -> dict[str, Any]:
    """Build the standard success payload."""
    return {
        "success": True,
        "data": data,
        "error": None,
    }


def build_error_payload(error: AmapCliError) -> dict[str, Any]:
    """Build the standard error payload."""
    return {
        "success": False,
        "data": None,
        "error": error.to_dict(),
    }


def write_json(payload: dict[str, Any], *, stream: TextIO | None = None) -> None:
    """Write a JSON payload as a single CLI response."""
    if stream is None:
        stream = sys.stdout
    json.dump(payload, stream, ensure_ascii=False, indent=2)
    stream.write("\n")


def emit_success(data: Any) -> None:
    """Print a success payload to standard output."""
    write_json(build_success_payload(data))


def emit_error(error: AmapCliError) -> None:
    """Print an error payload to standard output."""
    write_json(build_error_payload(error))
