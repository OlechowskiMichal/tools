"""Unit tests for gerrit module - config loading without os.environ mutation."""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest

from gerrit_review_parser.gerrit import (
    GerritConfig,
    build_ssh_command,
    load_gerrit_config,
)


def test_gerrit_config_immutable():
    """Test that GerritConfig is immutable (NamedTuple)."""
    config = GerritConfig(host="gerrit.example.com", port="29418", user="testuser")
    with pytest.raises(AttributeError):
        config.host = "other.example.com"


def test_gerrit_config_named_fields():
    """Test that GerritConfig has named fields accessible."""
    config = GerritConfig(host="gerrit.example.com", port="29418", user="testuser")
    assert config.host == "gerrit.example.com"
    assert config.port == "29418"
    assert config.user == "testuser"


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


def test_load_gerrit_config_from_file():
    """Test loading config from env file without mutating os.environ."""
    original_environ = dict(os.environ)

    with NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write('export GERRIT_HOST="file.gerrit.com"\n')
        f.write('export GERRIT_USER="fileuser"\n')
        f.write('export GERRIT_PORT="54321"\n')
        env_file = Path(f.name)

    try:
        config = load_gerrit_config(env={}, env_file=env_file)

        assert config.host == "file.gerrit.com"
        assert config.user == "fileuser"
        assert config.port == "54321"
        assert os.environ == original_environ
    finally:
        env_file.unlink()


def test_config_no_environ_mutation():
    """Verify that load_gerrit_config does not mutate os.environ."""
    original_keys = set(os.environ.keys())
    env = {
        "GERRIT_HOST": "test.gerrit.com",
        "GERRIT_USER": "testuser",
    }

    load_gerrit_config(env=env)

    assert set(os.environ.keys()) == original_keys


def test_build_ssh_command_structure():
    """Test that build_ssh_command produces correct command structure."""
    config = GerritConfig(host="gerrit.example.com", port="29418", user="testuser")
    cmd = build_ssh_command(config, "change:12345")

    assert cmd[0] == "ssh"
    assert "-p" in cmd
    assert "29418" in cmd
    assert "testuser@gerrit.example.com" in cmd
    assert "gerrit" in cmd
    assert "query" in cmd
    assert "--format=JSON" in cmd
    assert "change:12345" in cmd


def test_build_ssh_command_includes_flags():
    """Test that build_ssh_command includes all required query flags."""
    config = GerritConfig(host="gerrit.example.com", port="29418", user="testuser")
    cmd = build_ssh_command(config, "change:12345")

    assert "--patch-sets" in cmd
    assert "--files" in cmd
    assert "--comments" in cmd
