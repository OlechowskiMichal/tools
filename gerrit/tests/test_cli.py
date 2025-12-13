"""CLI integration tests for gerrit-review-parser."""

import json
import tempfile
from pathlib import Path

from click.testing import CliRunner

from gerrit_review_parser.cli import main


def test_version_flag():
    """Test that --version outputs version string."""
    runner = CliRunner()
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_help_flag():
    """Test that --help shows usage information."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Parse Gerrit review JSON" in result.output
    assert "--file" in result.output
    assert "--changeid" in result.output
    assert "--version" in result.output
    assert "--json" in result.output
    assert "--dry-run" in result.output


SAMPLE_JSON = """{
    "project": "test-project",
    "number": 12345,
    "subject": "Test commit",
    "patchSets": [
        {
            "number": 1,
            "comments": [
                {
                    "file": "src/main.py",
                    "line": 10,
                    "reviewer": {"name": "Reviewer"},
                    "message": "Fix this",
                    "unresolved": true
                }
            ]
        }
    ]
}"""


def test_json_flag_output():
    """Test that --json outputs valid JSON."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(SAMPLE_JSON)
        temp_file = Path(f.name)

    try:
        runner = CliRunner()
        result = runner.invoke(main, ["--file", str(temp_file), "--json"])
        assert result.exit_code == 0

        parsed = json.loads(result.output)
        assert "project" in parsed
        assert "change_number" in parsed
        assert "comments" in parsed
        assert parsed["project"] == "test-project"
    finally:
        temp_file.unlink()


def test_json_flag_comment_structure():
    """Test that --json output has correct comment structure."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(SAMPLE_JSON)
        temp_file = Path(f.name)

    try:
        runner = CliRunner()
        result = runner.invoke(main, ["--file", str(temp_file), "--json"])
        parsed = json.loads(result.output)

        assert len(parsed["comments"]) == 1
        comment = parsed["comments"][0]
        assert comment["file"] == "src/main.py"
        assert comment["line"] == 10
        assert comment["reviewer"] == "Reviewer"
        assert comment["unresolved"] is True
    finally:
        temp_file.unlink()


def test_dry_run_shows_command():
    """Test that --dry-run shows the SSH command that would be executed."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--changeid", "12345", "--dry-run"],
        env={
            "GERRIT_HOST": "gerrit.example.com",
            "GERRIT_USER": "testuser",
            "GERRIT_PORT": "29418",
        },
    )
    assert result.exit_code == 0
    assert "[DRY-RUN]" in result.output
    assert "ssh" in result.output
    assert "gerrit.example.com" in result.output
    assert "testuser" in result.output
    assert "change:12345" in result.output


def test_dry_run_with_query():
    """Test that --dry-run works with --query option."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--query", "status:open", "--dry-run"],
        env={
            "GERRIT_HOST": "gerrit.example.com",
            "GERRIT_USER": "testuser",
        },
    )
    assert result.exit_code == 0
    assert "[DRY-RUN]" in result.output
    assert "status:open" in result.output


def test_dry_run_with_json():
    """Test that --dry-run combined with --json outputs JSON format."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["--changeid", "12345", "--dry-run", "--json"],
        env={
            "GERRIT_HOST": "gerrit.example.com",
            "GERRIT_USER": "testuser",
        },
    )
    assert result.exit_code == 0

    parsed = json.loads(result.output)
    assert "dry_run" in parsed
    assert parsed["dry_run"] is True
    assert "command" in parsed
    assert "ssh" in parsed["command"]
