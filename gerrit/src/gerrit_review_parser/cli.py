"""CLI entry point for gerrit-review-parser."""

import sys
from datetime import datetime

import click

from .gerrit import fetch_from_gerrit
from .parser import parse_json_content, extract_comments, display_review


@click.command()
@click.option('--file', '-f', 'review_file', type=click.Path(exists=True),
              help='Path to Gerrit review JSON file')
@click.option('--changeid', '-c', type=str, help='Gerrit change ID to fetch and parse')
@click.option('--query', '-q', type=str, help='Gerrit query string to fetch and parse')
@click.option('--save', '-s', is_flag=True, help='Save fetched JSON to file')
@click.option('--output', '-o', type=str, help='Custom output filename (use with --save)')
@click.option('--debug', 'debug_mode', is_flag=True, help='Enable debug output')
@click.option('--unresolved-only', '-u', is_flag=True, help='Show only unresolved comments')
def main(review_file, changeid, query, save, output, debug_mode, unresolved_only):
    """Parse Gerrit review JSON and display comments with file context.

    Examples:
        gerrit-review-parser --changeid 12345
        gerrit-review-parser --file review.json --unresolved-only
        gerrit-review-parser --query "status:open project:myproject" --save
    """
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
    display_review(data, comments, unresolved_only, debug_mode)


if __name__ == "__main__":
    main()
