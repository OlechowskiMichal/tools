"""CLI entry point for gerrit-review-parser."""

import json
import sys
from datetime import datetime
from typing import NoReturn

import click

from . import __version__
from .gerrit import build_ssh_command, fetch_from_gerrit, load_gerrit_config
from .parser import display_review, extract_comments, output_as_dict, parse_json_content


def _fatal_exit(msg: str) -> NoReturn:
    """Print fatal error and exit."""
    print(f"FATAL: {msg}", file=sys.stderr)
    sys.exit(1)


def _debug(msg: str, enabled: bool) -> None:
    """Print debug message if enabled."""
    if enabled:
        print(f"[DEBUG] {msg}", file=sys.stderr)


def _normalize_changeid(changeid: str) -> str:
    """Ensure changeid has 'change:' prefix."""
    if not changeid.startswith("change:"):
        return f"change:{changeid}"
    return changeid


def _handle_dry_run(changeid: str | None, query: str | None, json_output: bool) -> None:
    """Handle dry-run mode: show command without executing."""
    query_str = _normalize_changeid(changeid) if changeid else query
    config = load_gerrit_config()
    cmd = build_ssh_command(config, query_str)
    cmd_str = " ".join(cmd)

    if json_output:
        print(json.dumps({"dry_run": True, "command": cmd_str}, indent=2))
    else:
        print(f"[DRY-RUN] Would execute: {cmd_str}")


def _load_from_file(filepath: str, debug: bool) -> str:
    """Load JSON content from file."""
    _debug(f"Loading review from file: {filepath}", debug)
    try:
        with open(filepath) as f:
            return f.read()
    except Exception as e:
        _fatal_exit(f"Cannot read {filepath}: {e}")


def _fetch_and_save(
    query_str: str, save: bool, output: str | None, filename_prefix: str, debug: bool
) -> str:
    """Fetch from Gerrit and optionally save to file."""
    json_content = fetch_from_gerrit(query_str, debug)

    if save:
        if filename_prefix.startswith("change:"):
            default_name = f"review-{filename_prefix.replace('change:', '')}.json"
        else:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"query-{timestamp}.json"

        filename = output or default_name
        with open(filename, "w") as f:
            f.write(json_content)
        print(f"Saved JSON to: {filename}")

    return json_content


def _load_json_content(
    review_file: str | None,
    changeid: str | None,
    query: str | None,
    save: bool,
    output: str | None,
    debug: bool,
) -> str:
    """Load JSON content from file, Gerrit, or stdin."""
    if review_file:
        return _load_from_file(review_file, debug)

    if changeid:
        _debug(f"Fetching change ID: {changeid}", debug)
        query_str = _normalize_changeid(changeid)
        return _fetch_and_save(query_str, save, output, query_str, debug)

    if query:
        _debug(f"Fetching query: {query}", debug)
        return _fetch_and_save(query, save, output, "query", debug)

    _debug("Reading from stdin", debug)
    return sys.stdin.read()


def _output_result(data: dict, comments: list, json_output: bool, unresolved_only: bool, debug: bool) -> None:
    """Output results as JSON or human-readable format."""
    if json_output:
        result = output_as_dict(data, comments)
        print(json.dumps(result, indent=2))
    else:
        display_review(data, comments, unresolved_only, debug)


@click.command()
@click.version_option(version=__version__, prog_name="gerrit-review-parser")
@click.option(
    "--file", "-f", "review_file",
    type=click.Path(exists=True),
    help="Path to Gerrit review JSON file",
)
@click.option("--changeid", "-c", type=str, help="Gerrit change ID to fetch and parse")
@click.option("--query", "-q", type=str, help="Gerrit query string to fetch and parse")
@click.option("--save", "-s", is_flag=True, help="Save fetched JSON to file")
@click.option("--output", "-o", type=str, help="Custom output filename (use with --save)")
@click.option("--debug", "debug_mode", is_flag=True, help="Enable debug output")
@click.option("--unresolved-only", "-u", is_flag=True, help="Show only unresolved comments")
@click.option("--json", "json_output", is_flag=True, help="Output as JSON for machine processing")
@click.option("--dry-run", is_flag=True, help="Show SSH command without executing")
def main(
    review_file, changeid, query, save, output, debug_mode, unresolved_only, json_output, dry_run
):
    """Parse Gerrit review JSON and display comments with file context.

    Examples:
        gerrit-review-parser --changeid 12345
        gerrit-review-parser --file review.json --unresolved-only
        gerrit-review-parser --query "status:open project:myproject" --save
        gerrit-review-parser --changeid 12345 --dry-run
    """
    if dry_run and (changeid or query):
        _handle_dry_run(changeid, query, json_output)
        return

    json_content = _load_json_content(review_file, changeid, query, save, output, debug_mode)

    if not json_content:
        _fatal_exit("No input provided")

    data = parse_json_content(json_content)
    comments = extract_comments(data, unresolved_only, debug_mode)
    _output_result(data, comments, json_output, unresolved_only, debug_mode)


if __name__ == "__main__":
    main()
