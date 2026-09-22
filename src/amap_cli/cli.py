"""CLI entrypoint and command registration."""

from __future__ import annotations

import argparse
from typing import Any, Sequence

from amap_cli.config import get_config_path, load_config, save_config
from amap_cli.distance import register_distance_command
from amap_cli.errors import AmapCliError, ValidationError
from amap_cli.geocode_command import register_geocode_command
from amap_cli.output import emit_error, emit_success
from amap_cli.route import register_route_command
from amap_cli.search_poi import register_search_poi_command
from amap_cli.skill import register_install_skill_command


class JsonArgumentParser(argparse.ArgumentParser):
    """Argument parser that routes validation failures to JSON output."""

    def error(self, message: str) -> None:
        raise ValidationError(message)


def build_parser() -> JsonArgumentParser:
    """Create the root CLI parser."""
    parser = JsonArgumentParser(
        prog="amap-cli",
        description="纯命令行高德地图 CLI 基础工具。",
    )
    subparsers = parser.add_subparsers(dest="command")

    _register_config_command(subparsers)
    register_install_skill_command(subparsers)
    register_geocode_command(subparsers)
    register_distance_command(subparsers)
    register_route_command(subparsers)
    register_search_poi_command(subparsers)
    return parser


def _register_config_command(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register configuration management commands."""
    parser = subparsers.add_parser("config", help="写入或查看高德 API 配置")
    parser.set_defaults(handler=_handle_config_root)

    config_subparsers = parser.add_subparsers(dest="config_command")

    set_parser = config_subparsers.add_parser("set", help="写入高德 API 配置")
    set_parser.add_argument("--api-key", "--key", dest="api_key", help="高德 API Key")
    set_parser.add_argument("--base-url", help="高德 API 基础地址")
    set_parser.add_argument(
        "--timeout-seconds",
        type=float,
        help="请求超时时间（秒）",
    )
    set_parser.add_argument(
        "--request-sleep-seconds",
        type=float,
        help="每次高德 API 调用结束后的 sleep 时间（秒，0 表示关闭）",
    )
    set_parser.set_defaults(handler=_handle_config_set)

    show_parser = config_subparsers.add_parser("show", help="查看当前配置（敏感信息脱敏）")
    show_parser.set_defaults(handler=_handle_config_show)


def _handle_config_root(_: argparse.Namespace) -> dict[str, Any]:
    """Show help when `config` is called without a subcommand."""
    raise ValidationError("缺少配置子命令，请使用 `config set` 或 `config show`。")


def _handle_config_set(args: argparse.Namespace) -> dict[str, Any]:
    """Persist configuration values."""
    if (
        args.api_key is None
        and args.base_url is None
        and args.timeout_seconds is None
        and args.request_sleep_seconds is None
    ):
        raise ValidationError(
            "请至少提供一个配置项，例如 `--api-key`、`--base-url`、`--timeout-seconds` 或 `--request-sleep-seconds`。"
        )

    config = save_config(
        api_key=args.api_key,
        base_url=args.base_url,
        timeout_seconds=args.timeout_seconds,
        request_sleep_seconds=args.request_sleep_seconds,
    )
    return {
        "message": "配置已保存。",
        "config_path": str(get_config_path()),
        "config": config.to_dict(mask_secrets=True),
    }


def _handle_config_show(_: argparse.Namespace) -> dict[str, Any]:
    """Display the current configuration with masked secrets."""
    config = load_config(required=False)
    return {
        "configured": config is not None and bool(config.api_key),
        "config_path": str(get_config_path()),
        "config": config.to_dict(mask_secrets=True) if config is not None else None,
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and emit unified JSON output for command results."""
    parser = build_parser()

    try:
        args = parser.parse_args(argv)
        if not hasattr(args, "handler"):
            parser.print_help()
            return 0

        result = args.handler(args)
        emit_success(result)
        return 0
    except AmapCliError as exc:
        emit_error(exc)
        return exc.exit_code
    except KeyboardInterrupt:
        error = AmapCliError("操作已取消。", code="INTERRUPTED", exit_code=130)
        emit_error(error)
        return error.exit_code
    except SystemExit:
        raise
    except Exception as exc:
        error = AmapCliError(
            "发生未预期错误。",
            code="UNEXPECTED_ERROR",
            details={"type": type(exc).__name__},
            exit_code=1,
        )
        emit_error(error)
        return error.exit_code
