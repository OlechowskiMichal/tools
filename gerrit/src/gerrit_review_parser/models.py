"""Data models for gerrit-review-parser."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Comment:
    """A single review comment (immutable)."""

    file: str
    line: int
    reviewer: str
    message: str
    unresolved: bool
