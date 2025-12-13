"""CLI entry point for gerrit-review-parser."""

import json
import sys
from datetime import datetime

import click

from . import __version__
from .gerrit import build_ssh_command, fetch_from_gerrit, load_gerrit_config
from .parser import display_review, extract_comments, output_as_dict, parse_json_content


@click.command()
@click.version_option(version=__version__, prog_name="gerrit-review-parser")
@click.option(
    "--file",
    "-f",
    "review_file",
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
        query_str = changeid if changeid else query
        if changeid and not changeid.startswith("change:"):
            query_str = f"change:{changeid}"
        config = load_gerrit_config()
        cmd = build_ssh_command(config, query_str)
        cmd_str = " ".join(cmd)

        if json_output:
            result = {"dry_run": True, "command": cmd_str}
            print(json.dumps(result, indent=2))
        else:
            print(f"[DRY-RUN] Would execute: {cmd_str}")
        return

    json_content = None

    if review_file:
        if debug_mode:
            print(f"[DEBUG] Loading review from file: {review_file}", file=sys.stderr)
        try:
            with open(review_file) as f:
                json_content = f.read()
        except Exception as e:
            print(f"FATAL: Cannot read {review_file}: {e}", file=sys.stderr)
            sys.exit(1)

    elif changeid:
        if debug_mode:
            print(f"[DEBUG] Fetching change ID: {changeid}", file=sys.stderr)
        if not changeid.startswith('change:'):
            changeid = f"change:{changeid}"
        json_content = fetch_from_gerrit(changeid, debug_mode)

        if save:
            change_num = changeid.replace('change:', '')
            filename = output or f"review-{change_num}.json"
            with open(filename, 'w') as f:
                f.write(json_content)
            print(f"Saved JSON to: {filename}")

    elif query:
        if debug_mode:
            print(f"[DEBUG] Fetching query: {query}", file=sys.stderr)
        json_content = fetch_from_gerrit(query, debug_mode)

        if save:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = output or f"query-{timestamp}.json"
            with open(filename, 'w') as f:
                f.write(json_content)
            print(f"Saved JSON to: {filename}")

    else:
        if debug_mode:
            print("[DEBUG] Reading from stdin", file=sys.stderr)
        json_content = sys.stdin.read()

    if not json_content:
        print("FATAL: No input provided", file=sys.stderr)
        sys.exit(1)

    data = parse_json_content(json_content)
    comments = extract_comments(data, unresolved_only, debug_mode)

    if json_output:
        result = output_as_dict(data, comments)
        print(json.dumps(result, indent=2))
    else:
        display_review(data, comments, unresolved_only, debug_mode)


if __name__ == "__main__":
    main()
