# Tools

Miscellaneous CLI tools and utilities.

## Available Tools

| Tool | Description | Install |
|------|-------------|---------|
| [gerrit](./gerrit/) | Parse Gerrit review JSON with file context | `uv tool install ./gerrit` |

## Installation

Each tool is self-contained. Install individually:

```bash
cd <tool-dir>
uv tool install .
```

## Adding New Tools

1. Create subdirectory with `pyproject.toml`
2. Add README.md with usage
3. Update this table
