"""SSH command builders for Gerrit operations."""

from .models import GerritConfig


def build_ssh_base(config: GerritConfig) -> list[str]:
    """Build base SSH command for Gerrit connection.

    Args:
        config: GerritConfig with connection details

    Returns:
        Base SSH command arguments
    """
    return [
        "ssh",
        "-p",
        config.port,
        f"{config.user}@{config.host}",
        "gerrit",
    ]


def build_query_command(
    config: GerritConfig,
    query_str: str,
    *,
    output_format: str = "JSON",
    include_patch_sets: bool = True,
    include_files: bool = True,
    include_comments: bool = True,
) -> list[str]:
    """Build SSH command for Gerrit query.

    Args:
        config: GerritConfig with connection details
        query_str: Gerrit query string
        output_format: Output format (JSON, TEXT)
        include_patch_sets: Include patch set information
        include_files: Include file information
        include_comments: Include comment information

    Returns:
        List of command arguments
    """
    cmd = build_ssh_base(config) + ["query", f"--format={output_format}"]

    if include_patch_sets:
        cmd.append("--patch-sets")
    if include_files:
        cmd.append("--files")
    if include_comments:
        cmd.append("--comments")

    cmd.append(query_str)
    return cmd
