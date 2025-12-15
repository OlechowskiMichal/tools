"""Configuration management for gerrit-review-parser."""

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

import tomli_w


class ConfigError(Exception):
    """Raised when configuration is missing or invalid."""


@dataclass(frozen=True)
class GerritConfig:
    """Gerrit connection configuration."""
    host: str
    port: str
    user: str


def get_config_path() -> Path:
    """Get the path to the configuration file.

    Returns:
        Path to ~/.config/gerrit-review-parser/config.toml
    """
    return Path.home() / ".config" / "gerrit-review-parser" / "config.toml"


def ensure_config_dir() -> None:
    """Create the configuration directory if it doesn't exist."""
    config_path = get_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)


def load_config_file() -> Optional[GerritConfig]:
    """Load configuration from TOML file.

    Returns:
        GerritConfig if file exists and is valid, None otherwise
    """
    config_path = get_config_path()

    if not config_path.exists():
        return None

    try:
        with open(config_path, "rb") as f:
            data = tomllib.load(f)

        if not all(key in data for key in ["host", "port", "user"]):
            return None

        return GerritConfig(
            host=data["host"],
            port=str(data["port"]),
            user=data["user"]
        )
    except (OSError, tomllib.TOMLDecodeError, KeyError, TypeError):
        return None


def load_env_config() -> Optional[GerritConfig]:
    """Load configuration from environment variables.

    Returns:
        GerritConfig if all required env vars are set, None otherwise
    """
    host = os.environ.get("GERRIT_HOST")
    port = os.environ.get("GERRIT_PORT")
    user = os.environ.get("GERRIT_USER")

    if host and port and user:
        return GerritConfig(host=host, port=port, user=user)

    return None


def load_config() -> GerritConfig:
    """Load configuration with precedence: env vars > config file.

    Returns:
        GerritConfig with effective configuration

    Raises:
        ConfigError: If no configuration is found
    """
    env_config = load_env_config()
    if env_config:
        return env_config

    file_config = load_config_file()
    if file_config:
        return file_config

    config_path = get_config_path()
    raise ConfigError(
        f"No configuration found. Please run 'gerrit-review-parser setup' "
        f"or set environment variables GERRIT_HOST, GERRIT_PORT, GERRIT_USER.\n"
        f"Expected config file: {config_path}"
    )


def save_config(config: GerritConfig) -> None:
    """Save configuration to TOML file.

    Args:
        config: GerritConfig to save
    """
    ensure_config_dir()
    config_path = get_config_path()

    data = {
        "host": config.host,
        "port": config.port,
        "user": config.user,
    }

    with open(config_path, "wb") as f:
        tomli_w.dump(data, f)


def get_config_with_sources() -> tuple[GerritConfig, dict[str, str]]:
    """Load configuration and track the source of each value.

    Returns:
        Tuple of (GerritConfig, source_map) where source_map indicates
        'env' or 'file' for each configuration value
    """
    env_config = load_env_config()
    file_config = load_config_file()

    if not env_config and not file_config:
        raise ConfigError(
            "No configuration found. Please run 'gerrit-review-parser setup' "
            "or set environment variables GERRIT_HOST, GERRIT_PORT, GERRIT_USER."
        )

    host = os.environ.get("GERRIT_HOST")
    port = os.environ.get("GERRIT_PORT")
    user = os.environ.get("GERRIT_USER")

    sources = {}

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
        raise ConfigError("GERRIT_PORT not configured")

    if user:
        sources["user"] = "env"
    elif file_config:
        user = file_config.user
        sources["user"] = "file"
    else:
        raise ConfigError("GERRIT_USER not configured")

    config = GerritConfig(host=host, port=port, user=user)
    return config, sources
