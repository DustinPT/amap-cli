"""Configuration persistence for Amap API access."""

from __future__ import annotations

import json
import os
import platform
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from amap_cli.errors import ConfigError, MissingConfigError, ValidationError

APP_NAME = "amap-cli"
CONFIG_FILE_NAME = "config.json"
DEFAULT_BASE_URL = "https://restapi.amap.com"
DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_REQUEST_SLEEP_SECONDS = 0.34


@dataclass(slots=True)
class AmapConfig:
    """User configuration required by the CLI."""

    api_key: str | None = None
    base_url: str = DEFAULT_BASE_URL
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS
    request_sleep_seconds: float = DEFAULT_REQUEST_SLEEP_SECONDS

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "AmapConfig":
        """Create a config object from persisted JSON data."""
        api_key = raw.get("api_key")
        base_url = raw.get("base_url", DEFAULT_BASE_URL)
        timeout_seconds = raw.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)
        request_sleep_seconds = raw.get(
            "request_sleep_seconds",
            DEFAULT_REQUEST_SLEEP_SECONDS,
        )

        if api_key is not None and not isinstance(api_key, str):
            raise ConfigError("配置文件中的 api_key 格式无效。")
        if not isinstance(base_url, str) or not base_url.strip():
            raise ConfigError("配置文件中的 base_url 格式无效。")
        if not isinstance(timeout_seconds, (int, float)) or timeout_seconds <= 0:
            raise ConfigError("配置文件中的 timeout_seconds 格式无效。")
        if (
            not isinstance(request_sleep_seconds, (int, float))
            or request_sleep_seconds < 0
        ):
            raise ConfigError("配置文件中的 request_sleep_seconds 格式无效。")

        normalized_api_key = None
        if api_key is not None:
            normalized_api_key = api_key.strip() or None

        return cls(
            api_key=normalized_api_key,
            base_url=base_url.strip(),
            timeout_seconds=float(timeout_seconds),
            request_sleep_seconds=float(request_sleep_seconds),
        )

    def to_dict(self, *, mask_secrets: bool = False) -> dict[str, Any]:
        """Serialize the config for persistence or display."""
        payload = asdict(self)
        if mask_secrets:
            payload["api_key"] = mask_secret(self.api_key)
        return payload


def get_config_dir() -> Path:
    """Return the OS-specific configuration directory."""
    system_name = platform.system().lower()

    if system_name == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME

    if system_name == "windows":
        app_data = os.environ.get("APPDATA")
        if app_data:
            return Path(app_data) / APP_NAME
        return Path.home() / "AppData" / "Roaming" / APP_NAME

    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home) / APP_NAME
    return Path.home() / ".config" / APP_NAME


def get_config_path() -> Path:
    """Return the full configuration file path."""
    return get_config_dir() / CONFIG_FILE_NAME


def _merge_error_details(
    current: Any | None,
    *,
    path: Path,
    operation: str | None = None,
    exc: BaseException | None = None,
) -> dict[str, Any]:
    """Attach config file context to an error payload."""
    details = current.copy() if isinstance(current, dict) else {}
    details["path"] = str(path)
    if operation is not None:
        details["operation"] = operation
    if exc is not None:
        details["type"] = type(exc).__name__
        details["reason"] = str(exc)
    return details


def load_config(*, required: bool = False) -> AmapConfig | None:
    """Load config from disk, optionally requiring it to exist."""
    path = get_config_path()
    try:
        exists = path.exists()
    except OSError as exc:
        raise ConfigError(
            "检查配置文件状态失败。",
            details=_merge_error_details(None, path=path, operation="stat", exc=exc),
        ) from exc

    if not exists:
        if required:
            raise MissingConfigError(
                "未找到高德 API 配置，请先执行 `amap-cli config set --api-key <KEY>`。",
                details=_merge_error_details(None, path=path),
            )
        return None

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(
            "配置文件不是合法的 JSON。",
            details=_merge_error_details(None, path=path, operation="read", exc=exc),
        ) from exc
    except OSError as exc:
        raise ConfigError(
            "读取配置文件失败。",
            details=_merge_error_details(None, path=path, operation="read", exc=exc),
        ) from exc

    if not isinstance(raw, dict):
        raise ConfigError(
            "配置文件内容格式无效。",
            details=_merge_error_details(None, path=path),
        )

    try:
        return AmapConfig.from_dict(raw)
    except ConfigError as exc:
        exc.details = _merge_error_details(exc.details, path=path)
        raise


def save_config(
    *,
    api_key: str | None = None,
    base_url: str | None = None,
    timeout_seconds: float | None = None,
    request_sleep_seconds: float | None = None,
) -> AmapConfig:
    """Persist config updates to the OS-specific config path."""
    config = load_config(required=False) or AmapConfig()

    if api_key is not None:
        api_key = api_key.strip()
        if not api_key:
            raise ValidationError("`--api-key` 不能为空。")
        config.api_key = api_key

    if base_url is not None:
        base_url = base_url.strip()
        if not base_url:
            raise ValidationError("`--base-url` 不能为空。")
        config.base_url = base_url

    if timeout_seconds is not None:
        if timeout_seconds <= 0:
            raise ValidationError("`--timeout-seconds` 必须大于 0。")
        config.timeout_seconds = float(timeout_seconds)

    if request_sleep_seconds is not None:
        if request_sleep_seconds < 0:
            raise ValidationError("`--request-sleep-seconds` 不能小于 0。")
        config.request_sleep_seconds = float(request_sleep_seconds)

    path = get_config_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise ConfigError(
            "创建配置目录失败。",
            details=_merge_error_details(
                None,
                path=path.parent,
                operation="create_dir",
                exc=exc,
            ),
        ) from exc

    try:
        path.write_text(
            json.dumps(config.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise ConfigError(
            "写入配置文件失败。",
            details=_merge_error_details(None, path=path, operation="write", exc=exc),
        ) from exc

    if os.name != "nt":
        try:
            path.chmod(0o600)
        except OSError:
            pass

    return config


def mask_secret(value: str | None) -> str | None:
    """Mask a secret for display in CLI output."""
    if value is None:
        return None
    if len(value) <= 4:
        return "*" * len(value)
    return "*" * (len(value) - 4) + value[-4:]
