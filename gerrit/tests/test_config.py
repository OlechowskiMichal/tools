"""Unit tests for config module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from gerrit_review_parser.config import (
    ConfigError,
    GerritConfig,
    ensure_config_dir,
    get_config_path,
    get_config_with_sources,
    load_config,
    load_config_file,
    load_env_config,
    save_config,
)


@pytest.fixture
def temp_config_dir(tmp_path, monkeypatch):
    """Create a temporary config directory."""
    config_dir = tmp_path / ".config" / "gerrit-review-parser"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.toml"

    monkeypatch.setattr("gerrit_review_parser.config.get_config_path", lambda: config_path)
    return config_dir


@pytest.fixture
def clean_env(monkeypatch):
    """Remove Gerrit-related environment variables."""
    monkeypatch.delenv("GERRIT_HOST", raising=False)
    monkeypatch.delenv("GERRIT_PORT", raising=False)
    monkeypatch.delenv("GERRIT_USER", raising=False)


class TestGerritConfig:
    """Test GerritConfig dataclass."""

    def test_frozen_dataclass(self):
        """Test that GerritConfig is frozen."""
        config = GerritConfig(host="example.com", port="29418", user="testuser")
        with pytest.raises(AttributeError):
            config.host = "different.com"

    def test_fields(self):
        """Test GerritConfig fields."""
        config = GerritConfig(host="example.com", port="29418", user="testuser")
        assert config.host == "example.com"
        assert config.port == "29418"
        assert config.user == "testuser"


class TestConfigPath:
    """Test config path functions."""

    def test_get_config_path(self):
        """Test get_config_path returns expected path."""
        path = get_config_path()
        assert path == Path.home() / ".config" / "gerrit-review-parser" / "config.toml"

    def test_ensure_config_dir_creates_directory(self, tmp_path, monkeypatch):
        """Test ensure_config_dir creates directory."""
        config_path = tmp_path / ".config" / "gerrit-review-parser" / "config.toml"
        monkeypatch.setattr("gerrit_review_parser.config.get_config_path", lambda: config_path)

        assert not config_path.parent.exists()
        ensure_config_dir()
        assert config_path.parent.exists()

    def test_ensure_config_dir_idempotent(self, temp_config_dir):
        """Test ensure_config_dir is idempotent."""
        ensure_config_dir()
        ensure_config_dir()
        assert temp_config_dir.exists()


class TestLoadConfigFile:
    """Test load_config_file function."""

    def test_no_file_returns_none(self, temp_config_dir, clean_env):
        """Test load_config_file returns None when file doesn't exist."""
        assert load_config_file() is None

    def test_valid_file_returns_config(self, temp_config_dir, clean_env):
        """Test load_config_file returns config from valid file."""
        config_path = temp_config_dir / "config.toml"
        config_path.write_text('[gerrit]\nhost = "example.com"\nport = "29418"\nuser = "testuser"\n')

        with patch("gerrit_review_parser.config.get_config_path", return_value=config_path):
            config_path.write_text('host = "example.com"\nport = "29418"\nuser = "testuser"\n')
            result = load_config_file()

        assert result is not None
        assert result.host == "example.com"
        assert result.port == "29418"
        assert result.user == "testuser"

    def test_missing_fields_returns_none(self, temp_config_dir, clean_env):
        """Test load_config_file returns None when required fields missing."""
        config_path = temp_config_dir / "config.toml"
        config_path.write_text('host = "example.com"\n')

        result = load_config_file()
        assert result is None

    def test_invalid_toml_returns_none(self, temp_config_dir, clean_env):
        """Test load_config_file returns None for invalid TOML."""
        config_path = temp_config_dir / "config.toml"
        config_path.write_text('invalid toml content [[[')

        result = load_config_file()
        assert result is None


class TestLoadEnvConfig:
    """Test load_env_config function."""

    def test_no_env_vars_returns_none(self, clean_env):
        """Test load_env_config returns None when env vars not set."""
        assert load_env_config() is None

    def test_partial_env_vars_returns_none(self, clean_env, monkeypatch):
        """Test load_env_config returns None when only some env vars set."""
        monkeypatch.setenv("GERRIT_HOST", "example.com")
        monkeypatch.setenv("GERRIT_PORT", "29418")
        assert load_env_config() is None

    def test_all_env_vars_returns_config(self, clean_env, monkeypatch):
        """Test load_env_config returns config when all env vars set."""
        monkeypatch.setenv("GERRIT_HOST", "example.com")
        monkeypatch.setenv("GERRIT_PORT", "29418")
        monkeypatch.setenv("GERRIT_USER", "testuser")

        config = load_env_config()
        assert config is not None
        assert config.host == "example.com"
        assert config.port == "29418"
        assert config.user == "testuser"


class TestLoadConfig:
    """Test load_config function with precedence."""

    def test_no_config_raises_error(self, temp_config_dir, clean_env):
        """Test load_config raises ConfigError when no config available."""
        with pytest.raises(ConfigError) as exc_info:
            load_config()
        assert "No configuration found" in str(exc_info.value)
        assert "gerrit-review-parser setup" in str(exc_info.value)

    def test_env_vars_take_precedence(self, temp_config_dir, clean_env, monkeypatch):
        """Test environment variables take precedence over file."""
        config_path = temp_config_dir / "config.toml"
        config_path.write_text('host = "file-host.com"\nport = "1111"\nuser = "fileuser"\n')

        monkeypatch.setenv("GERRIT_HOST", "env-host.com")
        monkeypatch.setenv("GERRIT_PORT", "2222")
        monkeypatch.setenv("GERRIT_USER", "envuser")

        config = load_config()
        assert config.host == "env-host.com"
        assert config.port == "2222"
        assert config.user == "envuser"

    def test_file_used_when_no_env(self, temp_config_dir, clean_env):
        """Test config file is used when no env vars set."""
        config_path = temp_config_dir / "config.toml"
        config_path.write_text('host = "file-host.com"\nport = "29418"\nuser = "fileuser"\n')

        config = load_config()
        assert config.host == "file-host.com"
        assert config.port == "29418"
        assert config.user == "fileuser"


class TestSaveConfig:
    """Test save_config function."""

    def test_save_config_creates_file(self, temp_config_dir):
        """Test save_config creates config file."""
        config = GerritConfig(host="example.com", port="29418", user="testuser")
        save_config(config)

        config_path = temp_config_dir / "config.toml"
        assert config_path.exists()

        content = config_path.read_text()
        assert 'host = "example.com"' in content
        assert 'port = "29418"' in content
        assert 'user = "testuser"' in content

    def test_save_config_overwrites_existing(self, temp_config_dir):
        """Test save_config overwrites existing file."""
        config_path = temp_config_dir / "config.toml"
        config_path.write_text('host = "old-host.com"\nport = "1111"\nuser = "olduser"\n')

        new_config = GerritConfig(host="new-host.com", port="2222", user="newuser")
        save_config(new_config)

        content = config_path.read_text()
        assert 'host = "new-host.com"' in content
        assert 'port = "2222"' in content
        assert 'user = "newuser"' in content
        assert "old-host.com" not in content


class TestGetConfigWithSources:
    """Test get_config_with_sources function."""

    def test_no_config_raises_error(self, temp_config_dir, clean_env):
        """Test get_config_with_sources raises ConfigError when no config."""
        with pytest.raises(ConfigError):
            get_config_with_sources()

    def test_all_from_env(self, temp_config_dir, clean_env, monkeypatch):
        """Test get_config_with_sources when all values from env."""
        monkeypatch.setenv("GERRIT_HOST", "env-host.com")
        monkeypatch.setenv("GERRIT_PORT", "29418")
        monkeypatch.setenv("GERRIT_USER", "envuser")

        config, sources = get_config_with_sources()

        assert config.host == "env-host.com"
        assert config.port == "29418"
        assert config.user == "envuser"
        assert sources["host"] == "env"
        assert sources["port"] == "env"
        assert sources["user"] == "env"

    def test_all_from_file(self, temp_config_dir, clean_env):
        """Test get_config_with_sources when all values from file."""
        config_path = temp_config_dir / "config.toml"
        config_path.write_text('host = "file-host.com"\nport = "29418"\nuser = "fileuser"\n')

        config, sources = get_config_with_sources()

        assert config.host == "file-host.com"
        assert config.port == "29418"
        assert config.user == "fileuser"
        assert sources["host"] == "file"
        assert sources["port"] == "file"
        assert sources["user"] == "file"

    def test_mixed_sources(self, temp_config_dir, clean_env, monkeypatch):
        """Test get_config_with_sources with mixed env and file sources."""
        config_path = temp_config_dir / "config.toml"
        config_path.write_text('host = "file-host.com"\nport = "29418"\nuser = "fileuser"\n')

        monkeypatch.setenv("GERRIT_HOST", "env-host.com")

        config, sources = get_config_with_sources()

        assert config.host == "env-host.com"
        assert config.port == "29418"
        assert config.user == "fileuser"
        assert sources["host"] == "env"
        assert sources["port"] == "file"
        assert sources["user"] == "file"
