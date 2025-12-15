"""Gerrit SSH/API layer for fetching review data."""

import subprocess
import sys

from .config import ConfigError, load_config


def die(msg: str) -> None:
    """Print fatal error and exit."""
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


def fetch_from_gerrit(query_str: str, debug: bool = False) -> str:
    """Fetch review data from Gerrit using SSH command.

    Args:
        query_str: Gerrit query string (e.g., "change:12345")
        debug: Enable debug output

    Returns:
        Raw JSON response from Gerrit
    """
    try:
        config = load_config()
    except ConfigError as e:
        die(str(e))

    cmd = [
        'ssh', '-p', config.port,
        f'{config.user}@{config.host}',
        'gerrit', 'query',
        '--format=JSON',
        '--patch-sets',
        '--files',
        '--comments',
        query_str
    ]

    if debug:
        print(f"[DEBUG] Running: {' '.join(cmd)}", file=sys.stderr)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        die(f"Gerrit query failed: {e.stderr}")
    except Exception as e:
        die(f"Failed to run Gerrit query: {e}")
