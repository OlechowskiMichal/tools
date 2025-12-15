"""CLI entry point for gerrit-review-parser."""

import sys
from datetime import datetime

import click

from .config import (
    ConfigError,
    GerritConfig,
    get_config_path,
    get_config_with_sources,
    save_config,
)
from .gerrit import fetch_from_gerrit
from .parser import parse_json_content, extract_comments, display_review


@click.group()
def cli():
    """Parse Gerrit review JSON and display comments with file context."""


@cli.command()
@click.option('--file', '-f', 'review_file', type=click.Path(exists=True),
              help='Path to Gerrit review JSON file')
@click.option('--changeid', '-c', type=str, help='Gerrit change ID to fetch and parse')
@click.option('--query', '-q', type=str, help='Gerrit query string to fetch and parse')
@click.option('--save', '-s', is_flag=True, help='Save fetched JSON to file')
@click.option('--output', '-o', type=str, help='Custom output filename (use with --save)')
@click.option('--debug', 'debug_mode', is_flag=True, help='Enable debug output')
@click.option('--unresolved-only', '-u', is_flag=True, help='Show only unresolved comments')
def parse(review_file, changeid, query, save, output, debug_mode, unresolved_only):
    """Parse Gerrit review JSON and display comments with file context.

    Examples:
        gerrit-review-parser parse --changeid 12345
        gerrit-review-parser parse --file review.json --unresolved-only
        gerrit-review-parser parse --query "status:open project:myproject" --save
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


@cli.command()
def setup():
    """Configure Gerrit connection settings interactively.

    This command will prompt for your Gerrit server details and save them
    to a configuration file for future use.
    """
    click.echo("Gerrit Review Parser - Configuration Setup")
    click.echo("=" * 50)
    click.echo()

    host = click.prompt("Gerrit host (e.g., gerrit.example.com)", type=str)
    if not host.strip():
        click.echo("Error: Host cannot be empty", err=True)
        sys.exit(1)

    port = click.prompt("Gerrit SSH port", type=str, default="29418")
    if not port.strip():
        click.echo("Error: Port cannot be empty", err=True)
        sys.exit(1)

    try:
        port_num = int(port)
        if port_num < 1 or port_num > 65535:
            click.echo("Error: Port must be between 1 and 65535", err=True)
            sys.exit(1)
    except ValueError:
        click.echo("Error: Port must be a valid number", err=True)
        sys.exit(1)

    user = click.prompt("Gerrit username", type=str)
    if not user.strip():
        click.echo("Error: Username cannot be empty", err=True)
        sys.exit(1)

    config = GerritConfig(host=host.strip(), port=port.strip(), user=user.strip())

    try:
        save_config(config)
        config_path = get_config_path()
        click.echo()
        click.echo("Configuration saved successfully!")
        click.echo(f"Config file: {config_path}")
    except OSError as e:
        click.echo(f"Error saving configuration: {e}", err=True)
        sys.exit(1)


@cli.group()
def config():
    """Manage configuration settings."""


@config.command()
def show():
    """Display current configuration settings.

    Shows the effective configuration values and indicates whether each
    value comes from environment variables or the config file.
    """
    try:
        cfg, sources = get_config_with_sources()

        click.echo("Current Gerrit Configuration")
        click.echo("=" * 50)
        click.echo()
        click.echo(f"Host:     {cfg.host} (from {sources['host']})")
        click.echo(f"Port:     {cfg.port} (from {sources['port']})")
        click.echo(f"User:     {cfg.user} (from {sources['user']})")
        click.echo()

        if any(s == "file" for s in sources.values()):
            config_path = get_config_path()
            click.echo(f"Config file: {config_path}")

    except ConfigError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def main():
    """Entry point for the CLI."""
    cli(prog_name="gerrit-review-parser")


if __name__ == "__main__":
    main()
