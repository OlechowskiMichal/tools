"""Gerrit configuration loading and management."""

import os
import tomllib
from pathlib import Path

import tomli_w

from .errors import fatal_exit
from .models import GerritConfig

DEFAULT_PORT = "29418"
CONFIG_DIR = Path.home() / ".config" / "gerrit-review-parser"
CONFIG_FILE = CONFIG_DIR / "config.toml"


class ConfigError(Exception):
    """Raised when configuration is missing or invalid."""


def get_config_path() -> Path:
    """Get the path to the configuration file."""
    return CONFIG_FILE


def load_gerrit_config(
    env: dict[str, str] | None = None,
) -> GerritConfig:
    """Load Gerrit configuration from environment, then TOML file fallback.

    Precedence: Environment variables > TOML config file

    Args:
        env: Environment dict (defaults to os.environ copy)

    Returns:
        GerritConfig with host, port, user
    """
    env = dict(os.environ) if env is None else env

    host = env.get("GERRIT_HOST")
    port = env.get("GERRIT_PORT")
    user = env.get("GERRIT_USER")

    if host and user:
        return GerritConfig(host=host, port=port or DEFAULT_PORT, user=user)

    file_config = _load_config_file()
    if file_config:
        return GerritConfig(
            host=host or file_config.host,
            port=port or file_config.port,
            user=user or file_config.user,
        )

    fatal_exit(
        "Gerrit not configured. Run: gerrit-review-parser setup\n"
        "Or set environment variables: GERRIT_HOST, GERRIT_PORT, GERRIT_USER"
    )


def _load_config_file() -> GerritConfig | None:
    """Load configuration from TOML file.

    Returns:
        GerritConfig if file exists and is valid, None otherwise
    """
    if not CONFIG_FILE.exists():
        return None

    try:
        with open(CONFIG_FILE, "rb") as f:
            data = tomllib.load(f)

        if not all(key in data for key in ["host", "port", "user"]):
            return None

        return GerritConfig(
            host=data["host"],
            port=str(data["port"]),
            user=data["user"],
        )
    except (OSError, tomllib.TOMLDecodeError, KeyError, TypeError):
        return None


def save_config(config: GerritConfig) -> None:
    """Save configuration to TOML file.

    Args:
        config: GerritConfig to save
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    data = {
        "host": config.host,
        "port": config.port,
        "user": config.user,
    }

    with open(CONFIG_FILE, "wb") as f:
        tomli_w.dump(data, f)


def get_config_with_sources() -> tuple[GerritConfig, dict[str, str]]:
    """Load configuration and track the source of each value.

    Returns:
        Tuple of (GerritConfig, source_map) where source_map indicates
        'env' or 'file' for each configuration value

    Raises:
        ConfigError: If no configuration is found
    """
    env = dict(os.environ)
    file_config = _load_config_file()

    host = env.get("GERRIT_HOST")
    port = env.get("GERRIT_PORT")
    user = env.get("GERRIT_USER")

    sources: dict[str, str] = {}

    if host:
        sources["host"] = "env"
    elif file_config:
        host = file_config.host
        sources["host"] = "file"
    else:
        raise ConfigError("GERRIT_HOST not configured")

    if port:
        sources["port"] = "env"
    elif file_config:
        port = file_config.port
        sources["port"] = "file"
    else:
        port = DEFAULT_PORT
        sources["port"] = "default"

    if user:
        sources["user"] = "env"
    elif file_config:
        user = file_config.user
        sources["user"] = "file"
    else:
        raise ConfigError("GERRIT_USER not configured")

    return GerritConfig(host=host, port=port, user=user), sources
