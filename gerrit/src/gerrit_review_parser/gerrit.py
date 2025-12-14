"""Gerrit SSH/API layer for fetching review data."""

import logging
import subprocess

from .commands import build_query_command
from .config import load_gerrit_config
from .errors import fatal_exit
from .models import GerritConfig

logger = logging.getLogger(__name__)


def fetch_from_gerrit(
    query_str: str, config: GerritConfig | None = None
) -> str:
    """Fetch review data from Gerrit using SSH command.

    Args:
        query_str: Gerrit query string (e.g., "change:12345")
        config: Optional GerritConfig (loads from env if not provided)

    Returns:
        Raw JSON response from Gerrit
    """
    if config is None:
        config = load_gerrit_config()

    cmd = build_query_command(config, query_str)

    logger.debug(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        fatal_exit(f"Gerrit query failed: {e.stderr}")
    except Exception as e:
        fatal_exit(f"Failed to run Gerrit query: {e}")
