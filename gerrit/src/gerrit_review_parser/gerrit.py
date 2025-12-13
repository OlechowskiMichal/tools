"""Gerrit SSH/API layer for fetching review data."""

import os
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple


class GerritConfig(NamedTuple):
    """Immutable configuration for Gerrit SSH connection."""

    host: str
    port: str
    user: str


def die(msg: str) -> None:
    """Print fatal error and exit."""
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


def _parse_env_file(filepath: Path) -> dict[str, str]:
    """Parse environment file without mutating os.environ.

    Args:
        filepath: Path to the env file

    Returns:
        Dictionary of parsed key-value pairs
    """
    result = {}
    with open(filepath) as f:
        for line in f:
            if line.startswith("export "):
                key, value = line[7:].strip().split("=", 1)
                result[key] = value.strip('"')
    return result


def load_gerrit_config(
    env: dict[str, str] | None = None, env_file: Path | None = None
) -> GerritConfig:
    """Load Gerrit configuration from environment or ~/.env.gerrit.

    Pure function that reads from provided env dict or falls back to os.environ
    and env file. Does not mutate os.environ.

    Args:
        env: Optional environment dict (defaults to os.environ)
        env_file: Optional path to env file (defaults to ~/.env.gerrit)

    Returns:
        GerritConfig with host, port, user
    """
    if env is None:
        env = dict(os.environ)

    gerrit_host = env.get("GERRIT_HOST")
    gerrit_port = env.get("GERRIT_PORT", "29418")
    gerrit_user = env.get("GERRIT_USER")

    if not gerrit_host or not gerrit_user:
        file_path = env_file or Path.home() / ".env.gerrit"
        if not file_path.exists():
            die("Gerrit not configured. Run: utils setup gerrit")
        try:
            file_env = _parse_env_file(file_path)
            gerrit_host = gerrit_host or file_env.get("GERRIT_HOST")
            gerrit_user = gerrit_user or file_env.get("GERRIT_USER")
            gerrit_port = file_env.get("GERRIT_PORT", gerrit_port)
        except Exception as e:
            die(f"Failed to load Gerrit config: {e}")

    if not gerrit_host or not gerrit_user:
        die("Gerrit configuration incomplete")

    return GerritConfig(host=gerrit_host, port=gerrit_port, user=gerrit_user)


def build_ssh_command(config: GerritConfig, query_str: str) -> list[str]:
    """Build SSH command for Gerrit query.

    Args:
        config: GerritConfig with connection details
        query_str: Gerrit query string

    Returns:
        List of command arguments
    """
    return [
        "ssh",
        "-p",
        config.port,
        f"{config.user}@{config.host}",
        "gerrit",
        "query",
        "--format=JSON",
        "--patch-sets",
        "--files",
        "--comments",
        query_str,
    ]


def fetch_from_gerrit(
    query_str: str, debug: bool = False, config: GerritConfig | None = None
) -> str:
    """Fetch review data from Gerrit using SSH command.

    Args:
        query_str: Gerrit query string (e.g., "change:12345")
        debug: Enable debug output
        config: Optional GerritConfig (loads from env if not provided)

    Returns:
        Raw JSON response from Gerrit
    """
    if config is None:
        config = load_gerrit_config()

    cmd = build_ssh_command(config, query_str)

    if debug:
        print(f"[DEBUG] Running: {' '.join(cmd)}", file=sys.stderr)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        die(f"Gerrit query failed: {e.stderr}")
    except Exception as e:
        die(f"Failed to run Gerrit query: {e}")
