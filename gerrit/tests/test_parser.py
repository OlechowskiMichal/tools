"""Unit tests for parser module - functional quality verification."""

import json

from gerrit_review_parser.models import ReviewOutput
from gerrit_review_parser.parser import (
    extract_comments,
    parse_json_content,
)


def test_parse_json_content_simple():
    """Test parsing simple JSON content."""
    json_str = '{"project": "test", "number": 123}'
    result = parse_json_content(json_str)
    assert result["project"] == "test"
    assert result["number"] == 123


def test_parse_json_content_multi_object():
    """Test parsing Gerrit's multi-object format (extracts first object)."""
    json_str = '{"project": "test", "number": 123}\n{"type": "stats", "rowCount": 1}'
    result = parse_json_content(json_str)
    assert result["project"] == "test"
    assert "type" not in result


def test_extract_comments_deterministic(sample_parsed_data):
    """Test that extract_comments is deterministic - same input produces same output."""
    result1 = extract_comments(sample_parsed_data)
    result2 = extract_comments(sample_parsed_data)
    assert result1 == result2
    assert len(result1) == 3


def test_extract_comments_sorted(sample_parsed_data):
    """Test that comments are sorted by file then line."""
    comments = extract_comments(sample_parsed_data)
    assert comments[0].file == "src/main.py"
    assert comments[0].line == 10
    assert comments[1].file == "src/main.py"
    assert comments[1].line == 20
    assert comments[2].file == "src/utils.py"
    assert comments[2].line == 5


def test_extract_comments_unresolved_only(sample_parsed_data):
    """Test filtering to unresolved comments only."""
    comments = extract_comments(sample_parsed_data, unresolved_only=True)
    assert len(comments) == 2
    assert all(c.unresolved for c in comments)


def test_review_output_structure(sample_parsed_data):
    """Test that ReviewOutput.to_dict() returns expected structure."""
    comments = extract_comments(sample_parsed_data)
    result = ReviewOutput.from_gerrit_data(sample_parsed_data, comments).to_dict()

    assert "project" in result
    assert "change_number" in result
    assert "subject" in result
    assert "comments" in result
    assert isinstance(result["comments"], list)


def test_review_output_is_json_serializable(sample_parsed_data):
    """Test that ReviewOutput.to_dict() produces JSON-serializable output."""
    comments = extract_comments(sample_parsed_data)
    result = ReviewOutput.from_gerrit_data(sample_parsed_data, comments).to_dict()
    json_str = json.dumps(result)
    assert json_str is not None
    parsed = json.loads(json_str)
    assert parsed == result


def test_review_output_comment_structure(sample_parsed_data):
    """Test that comments in ReviewOutput.to_dict() have all required fields."""
    comments = extract_comments(sample_parsed_data)
    result = ReviewOutput.from_gerrit_data(sample_parsed_data, comments).to_dict()

    for comment in result["comments"]:
        assert "file" in comment
        assert "line" in comment
        assert "reviewer" in comment
        assert "message" in comment
        assert "unresolved" in comment


# --- Edge case tests (bug catchers) ---


def test_extract_comments_empty_patchsets():
    """Handle review with no patchSets gracefully."""
    data = {"project": "test", "number": 123}
    comments = extract_comments(data)
    assert comments == []


def test_extract_comments_no_comments_key():
    """Handle patchSet without comments key."""
    data = {"patchSets": [{"number": 1}]}
    comments = extract_comments(data)
    assert comments == []


def test_comment_missing_reviewer_skipped():
    """Comments without reviewer should be skipped, not crash."""
    data = {
        "patchSets": [{
            "comments": [{
                "file": "test.py",
                "line": 10,
                "message": "Fix this",
            }]
        }]
    }
    comments = extract_comments(data)
    assert comments == []


def test_comment_missing_message_skipped():
    """Comments without message should be skipped, not crash."""
    data = {
        "patchSets": [{
            "comments": [{
                "file": "test.py",
                "line": 10,
                "reviewer": {"name": "Someone"},
            }]
        }]
    }
    comments = extract_comments(data)
    assert comments == []


def test_comment_reviewer_missing_name_skipped():
    """Comments with reviewer but no name should be skipped."""
    data = {
        "patchSets": [{
            "comments": [{
                "file": "test.py",
                "line": 10,
                "reviewer": {},
                "message": "Fix this",
            }]
        }]
    }
    comments = extract_comments(data)
    assert comments == []
