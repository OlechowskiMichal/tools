"""Pytest configuration and fixtures for gerrit-review-parser tests."""

import pytest


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
    import json
    return json.loads(sample_gerrit_json)


@pytest.fixture
def gerrit_config():
    """Return test GerritConfig."""
    from gerrit_review_parser.gerrit import GerritConfig
    return GerritConfig(host="gerrit.example.com", port="29418", user="testuser")
