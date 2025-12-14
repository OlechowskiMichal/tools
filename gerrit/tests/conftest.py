"""Pytest configuration and fixtures for gerrit-review-parser tests."""

import json
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner


@pytest.fixture
def cli_runner():
    """Return Click test runner."""
    return CliRunner()


@pytest.fixture
def sample_gerrit_json():
    """Return sample Gerrit JSON response for testing."""
    return """{
    "project": "test-project",
    "branch": "master",
    "id": "I1234567890",
    "number": 12345,
    "subject": "Test commit subject",
    "owner": {"name": "Test Owner", "email": "owner@example.com"},
    "status": "NEW",
    "patchSets": [
        {
            "number": 1,
            "revision": "abc123",
            "comments": [
                {
                    "file": "src/main.py",
                    "line": 10,
                    "reviewer": {"name": "Reviewer One"},
                    "message": "Please fix this",
                    "unresolved": true
                },
                {
                    "file": "src/main.py",
                    "line": 20,
                    "reviewer": {"name": "Reviewer Two"},
                    "message": "Looks good",
                    "unresolved": false
                },
                {
                    "file": "src/utils.py",
                    "line": 5,
                    "reviewer": {"name": "Reviewer One"},
                    "message": "Add docstring",
                    "unresolved": true
                }
            ]
        }
    ]
}"""


@pytest.fixture
def sample_parsed_data(sample_gerrit_json):
    """Return parsed sample data."""
    return json.loads(sample_gerrit_json)


@pytest.fixture
def sample_json_file(sample_gerrit_json):
    """Create temp file with sample JSON, clean up after test."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        f.write(sample_gerrit_json)
        temp_path = Path(f.name)
    yield temp_path
    temp_path.unlink()


@pytest.fixture
def gerrit_env():
    """Return test Gerrit environment variables."""
    return {
        "GERRIT_HOST": "gerrit.example.com",
        "GERRIT_USER": "testuser",
        "GERRIT_PORT": "29418",
    }


@pytest.fixture
def gerrit_config():
    """Return test GerritConfig."""
    from gerrit_review_parser.models import GerritConfig
    return GerritConfig(host="gerrit.example.com", port="29418", user="testuser")
