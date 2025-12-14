"""Display formatting for review output."""

import logging
import os
from itertools import groupby

import click

from .io import read_lines
from .models import Comment

logger = logging.getLogger(__name__)


def display_review(
    data: dict,
    comments: list[Comment],
    unresolved_only: bool = False,
) -> None:
    """Display formatted review output."""
    project = data.get("project", "Unknown")
    change_number = data.get("number", "Unknown")
    subject = data.get("subject", "No subject")

    logger.debug(f"Project: {project}, Change: {change_number}")

    if not comments:
        click.echo("No file comments found in review")
        return

    click.echo(f"\n{'='*70}")
    click.echo(f"Review #{change_number}")
    click.echo(f"{subject}")
    click.echo(f"Project: {project}")
    if unresolved_only:
        click.echo(f"Unresolved Comments: {len(comments)}")
    else:
        click.echo(f"Comments: {len(comments)}")
    click.echo(f"{'='*70}")

    sorted_comments = sorted(comments, key=lambda c: (c.file, c.line))
    for file_path, file_comments in groupby(sorted_comments, key=lambda c: c.file):
        click.echo(f"\n{file_path}")
        click.echo("-" * 40)

        for comment in file_comments:
            status = " [UNRESOLVED]" if comment.unresolved else ""
            click.echo(f"\nL{comment.line:4d} | {comment.reviewer}{status}")
            click.echo(f"     | {comment.message}")

            if not comment.file.startswith("/"):
                show_code_context(comment.file, comment.line)


def show_code_context(filepath: str, line_num: int, context: int = 2) -> None:
    """Display code context around a comment."""
    logger.debug(f"Reading file: {filepath}")

    if not os.path.exists(filepath):
        logger.debug(f"File not found: {filepath}")
        return

    try:
        lines = read_lines(filepath)
        start = max(0, line_num - context - 1)
        end = min(len(lines), line_num + context)

        click.echo("")
        for i in range(start, end):
            marker = ">>>" if i == line_num - 1 else "   "
            click.echo(f"     {i+1:4d} {marker} {lines[i].rstrip()}")

    except Exception as e:
        logger.error(f"Cannot read {filepath}: {e}")
