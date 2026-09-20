"""Skill installation commands."""

from __future__ import annotations

import argparse
import shutil
from importlib import resources
from pathlib import Path
from typing import Any

from amap_cli.errors import AmapCliError


def register_install_skill_command(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register the bundled skill installation command."""
    parser = subparsers.add_parser(
        "install-skill",
        help="安装内置 skill 到指定目录",
    )
    parser.add_argument(
        "--dir",
        dest="target_dir",
        required=True,
        help="skill 安装根目录，例如 ~/.agents/skills",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="目标 skill 已存在时覆盖",
    )
    parser.set_defaults(handler=_handle_install_skill)


def _handle_install_skill(args: argparse.Namespace) -> dict[str, Any]:
    """Install the bundled skill into the requested directory."""
    skill_name = "amap-cli"
    source_dir = _resolve_bundled_skill_dir()
    target_root = Path(args.target_dir).expanduser().resolve()
    target_skill_dir = target_root / skill_name

    overwritten = False
    if target_skill_dir.exists():
        if not args.force:
            raise AmapCliError(
                f"目标目录已存在 skill：{target_skill_dir}",
                code="SKILL_ALREADY_EXISTS",
                details={
                    "skill_path": str(target_skill_dir),
                    "hint": "如需覆盖，请追加 --force。",
                },
                exit_code=1,
            )
        if target_skill_dir.is_dir():
            shutil.rmtree(target_skill_dir)
        else:
            target_skill_dir.unlink()
        overwritten = True

    target_root.mkdir(parents=True, exist_ok=True)
    _copy_tree(source_dir, target_skill_dir)

    return {
        "message": "skill 安装完成。",
        "skill_name": skill_name,
        "source": str(source_dir),
        "target_dir": str(target_root),
        "skill_path": str(target_skill_dir),
        "overwritten": overwritten,
    }


def _resolve_bundled_skill_dir() -> Any:
    """Locate the bundled skill directory in installed or source layouts."""
    packaged_skill_dir = resources.files("amap_cli").joinpath("skills", "amap-cli")
    packaged_skill_file = packaged_skill_dir.joinpath("SKILL.md")
    if packaged_skill_file.is_file():
        return packaged_skill_dir

    repo_skill_dir = Path(__file__).resolve().parents[2] / "skills" / "amap-cli"
    if repo_skill_dir.is_dir():
        return repo_skill_dir

    raise AmapCliError(
        "未找到内置 skill 资源。",
        code="SKILL_RESOURCE_NOT_FOUND",
        details={"skill_name": "amap-cli"},
        exit_code=1,
    )


def _copy_tree(source_dir: Any, target_dir: Path) -> None:
    """Recursively copy the skill directory into the target path."""
    target_dir.mkdir(parents=True, exist_ok=True)
    for source_path in source_dir.iterdir():
        target_path = target_dir / source_path.name
        if source_path.is_dir():
            _copy_tree(source_path, target_path)
            continue
        with source_path.open("rb") as source_file, target_path.open("wb") as target_file:
            shutil.copyfileobj(source_file, target_file)
