"""Core parsing logic for Gerrit review JSON."""

import json
import logging
import os
import sys
from itertools import groupby

from .models import Comment

logger = logging.getLogger(__name__)


def parse_json_content(json_content: str) -> dict:
    """Parse JSON content, handling Gerrit's multi-object format.

    Gerrit sometimes appends stats as a second JSON object.
    This extracts just the first complete JSON object.

    Args:
        json_content: Raw JSON string from Gerrit

    Returns:
        Parsed JSON dictionary
    """
    try:
        depth = 0
        in_string = False
        escape = False
        for i, char in enumerate(json_content):
            if escape:
                escape = False
                continue
            if char == '\\':
                escape = True
                continue
            if char == '"' and not escape:
                in_string = not in_string
            if not in_string:
                if char == '{':
                    depth += 1
                elif char == '}':
                    depth -= 1
                    if depth == 0:
                        return json.loads(json_content[:i+1])
        return json.loads(json_content)
    except json.JSONDecodeError as e:
        logger.fatal(f"Invalid JSON: {e}")
        sys.exit(1)


def extract_comments(
    data: dict, unresolved_only: bool = False, debug: bool = False
) -> list[Comment]:
    """Extract file comments from parsed Gerrit data.

    Pure function using comprehensions and sorted() instead of mutable patterns.

    Args:
        data: Parsed Gerrit JSON
        unresolved_only: Filter to only unresolved comments
        debug: Enable debug output

    Returns:
        List of Comment objects sorted by file and line
    """
    if debug:
        for ps in data.get("patchSets", []):
            logger.debug(f"Checking patch set {ps.get('number', 0)}")

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


def output_as_dict(data: dict, comments: list[Comment]) -> dict:
    """Convert review data to dictionary for JSON output.

    Pure function returning review metadata and comments as a dict.

    Args:
        data: Parsed Gerrit JSON
        comments: List of extracted comments

    Returns:
        Dictionary with project, change_number, subject, and comments
    """
    return {
        "project": data.get("project", "Unknown"),
        "change_number": data.get("number", "Unknown"),
        "subject": data.get("subject", "No subject"),
        "comments": [
            {
                "file": c.file,
                "line": c.line,
                "reviewer": c.reviewer,
                "message": c.message,
                "unresolved": c.unresolved,
            }
            for c in comments
        ],
    }


def display_review(
    data: dict,
    comments: list[Comment],
    unresolved_only: bool = False,
    debug: bool = False,
) -> None:
    """Display formatted review output.

    Uses itertools.groupby for file grouping instead of mutable current_file.

    Args:
        data: Parsed Gerrit JSON
        comments: List of extracted comments
        unresolved_only: Whether filtering is active
        debug: Enable debug output
    """
    project = data.get("project", "Unknown")
    change_number = data.get("number", "Unknown")
    subject = data.get("subject", "No subject")

    logger.debug(f"Project: {project}, Change: {change_number}")

    if not comments:
        print("No file comments found in review")
        return

    print(f"\n{'='*70}")
    print(f"Review #{change_number}")
    print(f"{subject}")
    print(f"Project: {project}")
    if unresolved_only:
        print(f"Unresolved Comments: {len(comments)}")
    else:
        print(f"Comments: {len(comments)}")
    print(f"{'='*70}")

    for file_path, file_comments in groupby(comments, key=lambda c: c.file):
        print(f"\n{file_path}")
        print("-" * 40)

        for comment in file_comments:
            status = " [UNRESOLVED]" if comment.unresolved else ""
            print(f"\nL{comment.line:4d} | {comment.reviewer}{status}")
            print(f"     | {comment.message}")

            if not comment.file.startswith("/"):
                _show_code_context(comment.file, comment.line)


# --- Private helpers ---


def _extract_comment(comment_data: dict) -> Comment | None:
    """Extract a Comment from raw comment data.

    Args:
        comment_data: Raw comment dict from Gerrit JSON

    Returns:
        Comment if valid, None otherwise
    """
    if "file" not in comment_data or "line" not in comment_data:
        return None
    return Comment(
        file=comment_data["file"],
        line=comment_data["line"],
        reviewer=comment_data["reviewer"]["name"],
        message=comment_data["message"],
        unresolved=comment_data.get("unresolved", True),
    )


def _show_code_context(filepath: str, line_num: int, context: int = 2) -> None:
    """Display code context around a comment.

    Args:
        filepath: Path to the file
        line_num: Line number of the comment
        context: Number of lines before/after to show
    """
    logger.debug(f"Reading file: {filepath}")

    if not os.path.exists(filepath):
        logger.debug(f"File not found: {filepath}")
        return

    try:
        with open(filepath) as f:
            lines = f.readlines()

        start = max(0, line_num - context - 1)
        end = min(len(lines), line_num + context)

        print("")
        for i in range(start, end):
            marker = ">>>" if i == line_num - 1 else "   "
            print(f"     {i+1:4d} {marker} {lines[i].rstrip()}")

    except Exception as e:
        logger.error(f"Cannot read {filepath}: {e}")
