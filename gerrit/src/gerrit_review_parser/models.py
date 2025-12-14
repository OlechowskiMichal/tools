"""Data models for gerrit-review-parser."""

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class GerritConfig:
    """Immutable configuration for Gerrit SSH connection."""

    host: str
    port: str
    user: str


@dataclass(frozen=True)
class Comment:
    """A single review comment (immutable)."""

    file: str
    line: int
    reviewer: str
    message: str
    unresolved: bool


@dataclass(frozen=True)
class ReviewOutput:
    """Output structure for JSON serialization."""

    project: str
    change_number: int | str
    subject: str
    comments: tuple[Comment, ...]

    @classmethod
    def from_gerrit_data(cls, data: dict, comments: list[Comment]) -> "ReviewOutput":
        return cls(
            project=data.get("project", "Unknown"),
            change_number=data.get("number", "Unknown"),
            subject=data.get("subject", "No subject"),
            comments=tuple(comments),
        )

    def to_dict(self) -> dict:
        result = asdict(self)
        result["comments"] = list(result["comments"])
        return result
