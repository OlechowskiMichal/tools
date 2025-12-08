# Gerrit Review Parser

Parse Gerrit review JSON and display comments with file context.

## Installation

```bash
# Using uv
uv tool install .

# Using pip
pip install -e .
```

## Configuration

Create `~/.env.gerrit`:

```bash
export GERRIT_HOST="gerrit.example.com"
export GERRIT_PORT="29418"
export GERRIT_USER="your-username"
```

Or set environment variables directly.

## Usage

```bash
# Fetch and parse a change by ID
gerrit-review-parser --changeid 12345

# Parse a local JSON file
gerrit-review-parser --file review.json

# Show only unresolved comments
gerrit-review-parser --changeid 12345 --unresolved-only

# Fetch and save JSON for later
gerrit-review-parser --changeid 12345 --save

# Custom query
gerrit-review-parser --query "status:open project:myproject"

# Read from stdin
cat review.json | gerrit-review-parser
```

## Options

| Option | Short | Description |
|--------|-------|-------------|
| `--file` | `-f` | Path to Gerrit review JSON file |
| `--changeid` | `-c` | Gerrit change ID to fetch |
| `--query` | `-q` | Gerrit query string |
| `--save` | `-s` | Save fetched JSON to file |
| `--output` | `-o` | Custom output filename |
| `--unresolved-only` | `-u` | Show only unresolved comments |
| `--debug` | | Enable debug output |

## Output

```
======================================================================
Review #12345
Fix authentication bug in login handler
Project: myproject
Comments: 3
======================================================================

src/auth/login.py
----------------------------------------

L  42 | John Doe [UNRESOLVED]
     | Consider using constant-time comparison here

      40     def verify_password(self, password):
      41         stored_hash = self.get_hash()
      42 >>>     return stored_hash == hash(password)
      43
      44     def login(self, request):
```
