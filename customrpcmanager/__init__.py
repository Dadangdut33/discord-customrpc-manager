"""
CustomRPC Manager - A cross-platform Discord Rich Presence manager.

A production-ready application for manually controlling Discord RPC profiles
without relying on process detection.
"""

from importlib.metadata import PackageNotFoundError, version as package_version
from pathlib import Path


def get_app_version() -> str:
    """
    Get the application version.

    Prefer the local pyproject.toml when running from source, and fall back to
    installed package metadata when pyproject.toml is unavailable.
    """
    pyproject_path = Path(__file__).resolve().parent.parent / "pyproject.toml"
    if pyproject_path.exists():
        in_project_section = False
        for line in pyproject_path.read_text(encoding="utf-8").splitlines():
            stripped = line.strip()
            if stripped == "[project]":
                in_project_section = True
                continue

            if in_project_section and stripped.startswith("["):
                break

            if in_project_section and stripped.startswith("version ="):
                _, _, value = stripped.partition("=")
                return value.strip().strip('"').strip("'")

    try:
        return package_version("customrpcmanager")
    except PackageNotFoundError:
        return "unknown"
