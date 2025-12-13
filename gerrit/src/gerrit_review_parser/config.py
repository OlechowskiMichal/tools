"""Gerrit configuration loading."""

import os
from pathlib import Path

from .errors import fatal_exit
from .io import read_lines
from .models import GerritConfig

DEFAULT_PORT = "29418"
DEFAULT_ENV_FILE = Path.home() / ".env.gerrit"


def load_gerrit_config(
    env: dict[str, str] | None = None, env_file: Path | None = None
) -> GerritConfig:
    """Load Gerrit configuration from environment, then file fallback.

    Args:
        env: Environment dict (defaults to os.environ copy)
        env_file: Config file path (defaults to ~/.env.gerrit)

    Returns:
        GerritConfig with host, port, user
    """
    env = dict(os.environ) if env is None else env
    file_path = env_file or DEFAULT_ENV_FILE

    host = env.get("GERRIT_HOST")
    port = env.get("GERRIT_PORT")
    user = env.get("GERRIT_USER")

    if not (host and user):
        file_config = _load_config_file(file_path)
        host = host or file_config.get("GERRIT_HOST")
        port = port or file_config.get("GERRIT_PORT")
        user = user or file_config.get("GERRIT_USER")

    if not (host and user):
        fatal_exit("Gerrit configuration incomplete")

    return GerritConfig(host=host, port=port or DEFAULT_PORT, user=user)


def _load_config_file(file_path: Path) -> dict[str, str]:
    """Load config from file, exit on error."""
    if not file_path.exists():
        fatal_exit("Gerrit not configured. Run: utils setup gerrit")
    try:
        return _parse_env_file(file_path)
    except Exception as e:
        fatal_exit(f"Failed to load Gerrit config: {e}")


def _parse_env_file(filepath: Path) -> dict[str, str]:
    """Parse environment file without mutating os.environ."""
    return {
        key: value.strip('"')
        for line in read_lines(filepath)
        if line.startswith("export ")
        for key, value in [line[7:].strip().split("=", 1)]
    }
