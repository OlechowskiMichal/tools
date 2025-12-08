"""Gerrit SSH/API layer for fetching review data."""

import os
import subprocess
import sys
from pathlib import Path


def die(msg: str) -> None:
    """Print fatal error and exit."""
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


def load_gerrit_config() -> tuple[str, str, str]:
    """Load Gerrit configuration from environment or ~/.env.gerrit.

    Returns:
        Tuple of (host, port, user)
    """
    gerrit_host = os.environ.get('GERRIT_HOST')
    gerrit_port = os.environ.get('GERRIT_PORT', '29418')
    gerrit_user = os.environ.get('GERRIT_USER')

    if not gerrit_host or not gerrit_user:
        env_file = Path.home() / '.env.gerrit'
        if not env_file.exists():
            die("Gerrit not configured. Run: utils setup gerrit")
        try:
            with open(env_file) as f:
                for line in f:
                    if line.startswith('export '):
                        key, value = line[7:].strip().split('=', 1)
                        os.environ[key] = value.strip('"')
            gerrit_host = os.environ.get('GERRIT_HOST')
            gerrit_user = os.environ.get('GERRIT_USER')
            gerrit_port = os.environ.get('GERRIT_PORT', '29418')
        except Exception as e:
            die(f"Failed to load Gerrit config: {e}")

    if not gerrit_host or not gerrit_user:
        die("Gerrit configuration incomplete")

    return gerrit_host, gerrit_port, gerrit_user


def fetch_from_gerrit(query_str: str, debug: bool = False) -> str:
    """Fetch review data from Gerrit using SSH command.

    Args:
        query_str: Gerrit query string (e.g., "change:12345")
        debug: Enable debug output

    Returns:
        Raw JSON response from Gerrit
    """
    gerrit_host, gerrit_port, gerrit_user = load_gerrit_config()

    cmd = [
        'ssh', '-p', gerrit_port,
        f'{gerrit_user}@{gerrit_host}',
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
