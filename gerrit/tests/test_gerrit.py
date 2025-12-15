"""Unit tests for gerrit module - config loading without os.environ mutation."""

import os

import tomli_w

from gerrit_review_parser.commands import build_query_command
from gerrit_review_parser.config import load_gerrit_config, _load_config_file
from gerrit_review_parser.models import GerritConfig


def test_load_gerrit_config_from_env():
    """Test loading config from provided env dict without touching os.environ."""
    original_environ = dict(os.environ)
    env = {
        "GERRIT_HOST": "test.gerrit.com",
        "GERRIT_USER": "testuser",
        "GERRIT_PORT": "12345",
    }

    config = load_gerrit_config(env=env)

    assert config.host == "test.gerrit.com"
    assert config.user == "testuser"
    assert config.port == "12345"
    assert os.environ == original_environ


def test_load_gerrit_config_default_port():
    """Test that port defaults to 29418 if not specified."""
    env = {
        "GERRIT_HOST": "test.gerrit.com",
        "GERRIT_USER": "testuser",
    }

    config = load_gerrit_config(env=env)

    assert config.port == "29418"


def test_config_no_environ_mutation():
    """Verify that load_gerrit_config does not mutate os.environ."""
    original_keys = set(os.environ.keys())
    env = {
        "GERRIT_HOST": "test.gerrit.com",
        "GERRIT_USER": "testuser",
    }

    load_gerrit_config(env=env)

    assert set(os.environ.keys()) == original_keys


def test_build_query_command_structure():
    """Test that build_query_command produces correct command structure."""
    config = GerritConfig(host="gerrit.example.com", port="29418", user="testuser")
    cmd = build_query_command(config, "change:12345")

    assert cmd[0] == "ssh"
    assert "-p" in cmd
    assert "29418" in cmd
    assert "testuser@gerrit.example.com" in cmd
    assert "gerrit" in cmd
    assert "query" in cmd
    assert "--format=JSON" in cmd
    assert "change:12345" in cmd


def test_build_query_command_includes_flags():
    """Test that build_query_command includes all required query flags."""
    config = GerritConfig(host="gerrit.example.com", port="29418", user="testuser")
    cmd = build_query_command(config, "change:12345")

    assert "--patch-sets" in cmd
    assert "--files" in cmd
    assert "--comments" in cmd


def test_load_config_file_toml(monkeypatch, tmp_path):
    """Test loading config from TOML file."""
    config_dir = tmp_path / ".config" / "gerrit-review-parser"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.toml"

    data = {
        "host": "toml.gerrit.com",
        "port": "54321",
        "user": "tomluser",
    }
    with open(config_file, "wb") as f:
        tomli_w.dump(data, f)

    import gerrit_review_parser.config as config_module
    monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)

    result = _load_config_file()

    assert result is not None
    assert result.host == "toml.gerrit.com"
    assert result.port == "54321"
    assert result.user == "tomluser"


def test_load_config_file_missing_returns_none(monkeypatch, tmp_path):
    """Test that missing config file returns None."""
    config_file = tmp_path / "nonexistent" / "config.toml"

    import gerrit_review_parser.config as config_module
    monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)

    result = _load_config_file()
    assert result is None


def test_load_config_file_invalid_toml_returns_none(monkeypatch, tmp_path):
    """Test that invalid TOML file returns None."""
    config_dir = tmp_path / ".config" / "gerrit-review-parser"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.toml"

    with open(config_file, "w") as f:
        f.write("this is not valid toml [[[")

    import gerrit_review_parser.config as config_module
    monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)

    result = _load_config_file()
    assert result is None


def test_load_config_file_missing_keys_returns_none(monkeypatch, tmp_path):
    """Test that TOML file with missing required keys returns None."""
    config_dir = tmp_path / ".config" / "gerrit-review-parser"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.toml"

    data = {"host": "gerrit.com"}  # missing port and user
    with open(config_file, "wb") as f:
        tomli_w.dump(data, f)

    import gerrit_review_parser.config as config_module
    monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)

    result = _load_config_file()
    assert result is None


def test_env_takes_precedence_over_file(monkeypatch, tmp_path):
    """Test that environment variables take precedence over config file."""
    config_dir = tmp_path / ".config" / "gerrit-review-parser"
    config_dir.mkdir(parents=True)
    config_file = config_dir / "config.toml"

    data = {
        "host": "file.gerrit.com",
        "port": "11111",
        "user": "fileuser",
    }
    with open(config_file, "wb") as f:
        tomli_w.dump(data, f)

    import gerrit_review_parser.config as config_module
    monkeypatch.setattr(config_module, "CONFIG_FILE", config_file)

    env = {
        "GERRIT_HOST": "env.gerrit.com",
        "GERRIT_USER": "envuser",
    }

    config = load_gerrit_config(env=env)

    assert config.host == "env.gerrit.com"
    assert config.user == "envuser"
    assert config.port == "29418"  # DEFAULT_PORT, not file port
