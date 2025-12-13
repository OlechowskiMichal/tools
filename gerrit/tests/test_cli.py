"""CLI integration tests for gerrit-review-parser."""

import json

from gerrit_review_parser.cli import main


def test_version_flag(cli_runner):
    """Test that --version outputs version string."""
    result = cli_runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_help_flag(cli_runner):
    """Test that --help shows usage information."""
    result = cli_runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Parse Gerrit review JSON" in result.output
    assert "--file" in result.output
    assert "--changeid" in result.output
    assert "--version" in result.output
    assert "--json" in result.output
    assert "--dry-run" in result.output


def test_json_flag_output(cli_runner, sample_json_file):
    """Test that --json outputs valid JSON."""
    result = cli_runner.invoke(main, ["--file", str(sample_json_file), "--json"])
    assert result.exit_code == 0

    parsed = json.loads(result.output)
    assert "project" in parsed
    assert "change_number" in parsed
    assert "comments" in parsed
    assert parsed["project"] == "test-project"


def test_json_flag_comment_structure(cli_runner, sample_json_file):
    """Test that --json output has correct comment structure."""
    result = cli_runner.invoke(main, ["--file", str(sample_json_file), "--json"])
    parsed = json.loads(result.output)

    assert len(parsed["comments"]) == 3
    comment = parsed["comments"][0]
    assert comment["file"] == "src/main.py"
    assert comment["line"] == 10
    assert comment["reviewer"] == "Reviewer One"
    assert comment["unresolved"] is True


def test_dry_run_shows_command(cli_runner, gerrit_env):
    """Test that --dry-run shows the SSH command that would be executed."""
    result = cli_runner.invoke(
        main,
        ["--changeid", "12345", "--dry-run"],
        env=gerrit_env,
    )
    assert result.exit_code == 0
    assert "[DRY-RUN]" in result.output
    assert "ssh" in result.output
    assert "gerrit.example.com" in result.output
    assert "testuser" in result.output
    assert "change:12345" in result.output


def test_dry_run_with_query(cli_runner, gerrit_env):
    """Test that --dry-run works with --query option."""
    result = cli_runner.invoke(
        main,
        ["--query", "status:open", "--dry-run"],
        env=gerrit_env,
    )
    assert result.exit_code == 0
    assert "[DRY-RUN]" in result.output
    assert "status:open" in result.output


def test_dry_run_with_json(cli_runner, gerrit_env):
    """Test that --dry-run combined with --json outputs JSON format."""
    result = cli_runner.invoke(
        main,
        ["--changeid", "12345", "--dry-run", "--json"],
        env=gerrit_env,
    )
    assert result.exit_code == 0

    parsed = json.loads(result.output)
    assert "dry_run" in parsed
    assert parsed["dry_run"] is True
    assert "command" in parsed
    assert "ssh" in parsed["command"]
