"""Module entrypoint for `python -m amap_cli`."""

from __future__ import annotations

from amap_cli.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
