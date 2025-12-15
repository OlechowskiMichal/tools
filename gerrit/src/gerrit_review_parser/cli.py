"""CLI entry point for gerrit-review-parser."""

import json
import logging
import sys
from datetime import datetime

import click

from . import __version__
from .commands import build_query_command
from .config import (
    ConfigError,
    get_config_path,
    get_config_with_sources,
    load_gerrit_config,
    save_config,
)
from .display import display_review
from .errors import fatal_exit
from .gerrit import fetch_from_gerrit
from .io import read_file, write_file
from .models import Comment, GerritConfig, ReviewOutput
from .parser import extract_comments, parse_json_content

logger = logging.getLogger(__name__)


@click.group()
@click.version_option(version=__version__, prog_name="gerrit-review-parser")
def cli():
    """Parse Gerrit review JSON and display comments with file context."""


@cli.command()
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
def parse(
    review_file, changeid, query, save, output, debug_mode, unresolved_only, json_output, dry_run
):
    """Parse Gerrit review JSON and display comments with file context.

    Examples:
        gerrit-review-parser parse --changeid 12345
        gerrit-review-parser parse --file review.json --unresolved-only
        gerrit-review-parser parse --query "status:open project:myproject" --save
        gerrit-review-parser parse --changeid 12345 --dry-run
    """
    _setup_logging(debug_mode)

    if dry_run and review_file:
        logger.warning("--dry-run has no effect when reading from file")

    if dry_run and (changeid or query):
        _handle_dry_run(changeid, query, json_output)
        return

    json_content = _load_json_content(review_file, changeid, query, save, output)

    if not json_content:
        fatal_exit("No input provided")

    data = parse_json_content(json_content)
    comments = extract_comments(data, unresolved_only)
    _output_result(data, comments, json_output, unresolved_only)


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


@config.command(name="show")
def config_show():
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


# --- Private helpers ---


def _setup_logging(debug: bool) -> None:
    """Configure logging based on debug flag."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(message)s",
        stream=sys.stderr,
    )


def _normalize_changeid(changeid: str) -> str:
    """Ensure changeid has 'change:' prefix."""
    if not changeid.startswith("change:"):
        return f"change:{changeid}"
    return changeid


def _handle_dry_run(changeid: str | None, query: str | None, json_output: bool) -> None:
    """Handle dry-run mode: show command without executing."""
    query_str = _normalize_changeid(changeid) if changeid else query
    config = load_gerrit_config()
    cmd = build_query_command(config, query_str)
    cmd_str = " ".join(cmd)

    if json_output:
        click.echo(json.dumps({"dry_run": True, "command": cmd_str}, indent=2))
    else:
        click.echo(f"[DRY-RUN] Would execute: {cmd_str}")


def _load_from_file(filepath: str) -> str:
    """Load JSON content from file."""
    logger.debug(f"Loading review from file: {filepath}")
    try:
        return read_file(filepath)
    except Exception as e:
        fatal_exit(f"Cannot read {filepath}: {e}")


def _fetch_and_save(query_str: str, save: bool, output: str | None, filename_prefix: str) -> str:
    """Fetch from Gerrit and optionally save to file."""
    json_content = fetch_from_gerrit(query_str)

    if not save:
        return json_content

    default_name = (
        f"review-{filename_prefix.removeprefix('change:')}.json"
        if filename_prefix.startswith("change:")
        else f"query-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )

    filename = output or default_name
    write_file(filename, json_content)
    logger.info(f"Saved JSON to: {filename}")

    return json_content


def _load_json_content(
    review_file: str | None,
    changeid: str | None,
    query: str | None,
    save: bool,
    output: str | None,
) -> str:
    """Load JSON content from file, Gerrit, or stdin."""
    if review_file:
        return _load_from_file(review_file)

    if changeid:
        logger.debug(f"Fetching change ID: {changeid}")
        query_str = _normalize_changeid(changeid)
        return _fetch_and_save(query_str, save, output, query_str)

    if query:
        logger.debug(f"Fetching query: {query}")
        return _fetch_and_save(query, save, output, "query")

    if sys.stdin.isatty():
        return ""
    logger.debug("Reading from stdin")
    return sys.stdin.read()


def _output_result(
    data: dict, comments: list[Comment], json_output: bool, unresolved_only: bool
) -> None:
    """Output results as JSON or human-readable format."""
    if json_output:
        result = ReviewOutput.from_gerrit_data(data, comments).to_dict()
        click.echo(json.dumps(result, indent=2))
    else:
        display_review(data, comments, unresolved_only)


def main():
    """Entry point for the CLI."""
    cli(prog_name="gerrit-review-parser")


if __name__ == "__main__":
    main()
