"""Core parsing logic for Gerrit review JSON."""

import json
import logging

from .errors import fatal_exit
from .models import Comment

logger = logging.getLogger(__name__)


def parse_json_content(json_content: str) -> dict:
    """Parse JSON content, handling Gerrit's multi-object format.

    Gerrit sometimes appends stats as a second JSON object.
    Uses raw_decode() to extract just the first complete JSON object.

    Args:
        json_content: Raw JSON string from Gerrit

    Returns:
        Parsed JSON dictionary
    """
    try:
        return json.JSONDecoder().raw_decode(json_content)[0]
    except json.JSONDecodeError as e:
        fatal_exit(f"Invalid JSON: {e}")


def extract_comments(data: dict, unresolved_only: bool = False) -> list[Comment]:
    """Extract file comments from parsed Gerrit data.

    Pure function using comprehensions and sorted() instead of mutable patterns.

    Args:
        data: Parsed Gerrit JSON
        unresolved_only: Filter to only unresolved comments

    Returns:
        List of Comment objects sorted by file and line
    """
    raw_comments = [
        comment
        for patch_set in data.get("patchSets", [])
        for comment in patch_set.get("comments", [])
    ]

    comments = [c for c in (_extract_comment(r) for r in raw_comments) if c is not None]

    if unresolved_only:
        comments = [c for c in comments if c.unresolved]

    logger.debug(f"Found {len(comments)} file comments")

    return sorted(comments, key=lambda x: (x.file, x.line))


# --- Private helpers ---


def _extract_comment(comment_data: dict) -> Comment | None:
    """Extract a Comment from raw comment data.

    Args:
        comment_data: Raw comment dict from Gerrit JSON

    Returns:
        Comment if valid, None if missing required fields
    """
    try:
        return Comment(
            file=comment_data["file"],
            line=comment_data["line"],
            reviewer=comment_data["reviewer"]["name"],
            message=comment_data["message"],
            unresolved=comment_data.get("unresolved", True),
        )
    except (KeyError, TypeError):
        return None
