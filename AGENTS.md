# Agent Instructions: tools

## Overview

Collection of utility tools including gerrit-review-parser.

## Structure

```text
gerrit/                    # Gerrit review parser tool
├── src/gerrit_review_parser/
├── tests/
├── pyproject.toml
└── README.md
```

## Tech Stack

- Python 3.11+
- uv (package manager)
- pytest (testing)
- ruff (linting)

## Commands

```bash
# Install (gerrit)
cd gerrit && uv sync

# Run CLI
uv run python -m gerrit_review_parser.cli --help

# Test
uv run pytest

# Lint
uv run ruff check .
```

## Tools

- **gerrit-review-parser**: CLI for parsing and analyzing Gerrit code reviews
