"""Unit tests for parser module - functional quality verification."""

import json

import pytest

from gerrit_review_parser.parser import (
    Comment,
    extract_comments,
    output_as_dict,
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


def test_comment_immutability():
    """Test that Comment is frozen and cannot be modified."""
    comment = Comment(
        file="test.py",
        line=10,
        reviewer="Test",
        message="Fix this",
        unresolved=True,
    )
    with pytest.raises(AttributeError):
        comment.file = "other.py"
    with pytest.raises(AttributeError):
        comment.line = 20


def test_comment_hashable():
    """Test that frozen Comment is hashable (can be used in sets)."""
    comment1 = Comment(
        file="test.py", line=10, reviewer="Test", message="Fix", unresolved=True
    )
    comment2 = Comment(
        file="test.py", line=10, reviewer="Test", message="Fix", unresolved=True
    )
    comment_set = {comment1, comment2}
    assert len(comment_set) == 1


def test_output_as_dict_structure(sample_parsed_data):
    """Test that output_as_dict returns expected structure."""
    comments = extract_comments(sample_parsed_data)
    result = output_as_dict(sample_parsed_data, comments)

    assert "project" in result
    assert "change_number" in result
    assert "subject" in result
    assert "comments" in result
    assert isinstance(result["comments"], list)


def test_output_as_dict_is_json_serializable(sample_parsed_data):
    """Test that output_as_dict produces JSON-serializable output."""
    comments = extract_comments(sample_parsed_data)
    result = output_as_dict(sample_parsed_data, comments)
    json_str = json.dumps(result)
    assert json_str is not None
    parsed = json.loads(json_str)
    assert parsed == result


def test_output_as_dict_comment_structure(sample_parsed_data):
    """Test that comments in output_as_dict have all required fields."""
    comments = extract_comments(sample_parsed_data)
    result = output_as_dict(sample_parsed_data, comments)

    for comment in result["comments"]:
        assert "file" in comment
        assert "line" in comment
        assert "reviewer" in comment
        assert "message" in comment
        assert "unresolved" in comment
