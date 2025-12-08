"""Core parsing logic for Gerrit review JSON."""

import json
import os
import sys
from dataclasses import dataclass


@dataclass
class Comment:
    """A single review comment."""
    file: str
    line: int
    reviewer: str
    message: str
    unresolved: bool


def error(msg: str) -> None:
    """Print error message."""
    print(f"ERROR: {msg}", file=sys.stderr)


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
        print(f"FATAL: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)


def extract_comments(data: dict, unresolved_only: bool = False, debug: bool = False) -> list[Comment]:
    """Extract file comments from parsed Gerrit data.

    Args:
        data: Parsed Gerrit JSON
        unresolved_only: Filter to only unresolved comments
        debug: Enable debug output

    Returns:
        List of Comment objects sorted by file and line
    """
    comments = []

    for patch_set in data.get('patchSets', []):
        patch_num = patch_set.get('number', 0)
        if debug:
            print(f"[DEBUG] Checking patch set {patch_num}", file=sys.stderr)

        for comment in patch_set.get('comments', []):
            if 'file' in comment and 'line' in comment:
                is_unresolved = comment.get('unresolved', True)

                if unresolved_only and not is_unresolved:
                    continue

                comments.append(Comment(
                    file=comment['file'],
                    line=comment['line'],
                    reviewer=comment['reviewer']['name'],
                    message=comment['message'],
                    unresolved=is_unresolved
                ))

    if debug:
        print(f"[DEBUG] Found {len(comments)} file comments", file=sys.stderr)

    comments.sort(key=lambda x: (x.file, x.line))
    return comments


def show_code_context(filepath: str, line_num: int, debug: bool = False, context: int = 2) -> None:
    """Display code context around a comment.

    Args:
        filepath: Path to the file
        line_num: Line number of the comment
        debug: Enable debug output
        context: Number of lines before/after to show
    """
    if debug:
        print(f"[DEBUG] Reading file: {filepath}", file=sys.stderr)

    if not os.path.exists(filepath):
        if debug:
            print(f"[DEBUG] File not found: {filepath}", file=sys.stderr)
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
        error(f"Cannot read {filepath}: {e}")


def display_review(data: dict, comments: list[Comment], unresolved_only: bool = False, debug: bool = False) -> None:
    """Display formatted review output.

    Args:
        data: Parsed Gerrit JSON
        comments: List of extracted comments
        unresolved_only: Whether filtering is active
        debug: Enable debug output
    """
    project = data.get('project', 'Unknown')
    change_number = data.get('number', 'Unknown')
    subject = data.get('subject', 'No subject')

    if debug:
        print(f"[DEBUG] Project: {project}, Change: {change_number}", file=sys.stderr)

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

    current_file = None
    for comment in comments:
        if comment.file != current_file:
            current_file = comment.file
            print(f"\n{current_file}")
            print("-" * 40)

        status = " [UNRESOLVED]" if comment.unresolved else ""
        print(f"\nL{comment.line:4d} | {comment.reviewer}{status}")
        print(f"     | {comment.message}")

        if not comment.file.startswith('/'):
            show_code_context(comment.file, comment.line, debug)
