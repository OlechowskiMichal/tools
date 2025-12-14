"""File I/O utilities."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def read_file(filepath: str | Path) -> str:
    """Read entire file content.

    Args:
        filepath: Path to file

    Returns:
        File content as string

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    with open(filepath, encoding="utf-8") as f:
        return f.read()


def read_lines(filepath: str | Path) -> list[str]:
    """Read file as list of lines.

    Args:
        filepath: Path to file

    Returns:
        List of lines (with newlines intact)

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If file cannot be read
    """
    with open(filepath, encoding="utf-8") as f:
        return f.readlines()


def write_file(filepath: str | Path, content: str) -> None:
    """Write content to file.

    Args:
        filepath: Path to file
        content: Content to write
    """
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    logger.debug(f"Wrote {len(content)} characters to {filepath}")
