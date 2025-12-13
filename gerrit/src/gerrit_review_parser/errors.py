"""Error handling utilities."""

import logging
import sys
from typing import NoReturn

logger = logging.getLogger(__name__)


def fatal_exit(msg: str) -> NoReturn:
    """Log fatal error and exit."""
    logger.fatal(msg)
    sys.exit(1)
