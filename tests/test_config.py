"""Tests for config module."""
import json
import os
import tempfile
import pytest
from unittest.mock import patch


def test_default_config_values():
    """New config should have sensible defaults."""
    from config import Config
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = Config(app_dir=tmpdir)
        assert cfg.get("hotkey") == "ctrl+shift+d"
        assert cfg.get("theme") == "dark"
        assert cfg.get("start_on_boot") is False
        assert cfg.get("api_key") == ""


def test_save_and_load_config():
    """Config should persist to disk and reload."""
    from config import Config
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = Config(app_dir=tmpdir)
        cfg.set("theme", "light")
        cfg.save()

        cfg2 = Config(app_dir=tmpdir)
        assert cfg2.get("theme") == "light"


def test_api_key_encrypted_on_disk():
    """API key should not appear in plaintext in the config file."""
    from config import Config
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = Config(app_dir=tmpdir)
        cfg.set_api_key("sk-ant-test-key-12345")
        cfg.save()

        # Read raw file — key should NOT be plaintext
        raw = open(os.path.join(tmpdir, "config.json")).read()
        assert "sk-ant-test-key-12345" not in raw


def test_api_key_round_trip():
    """Encrypted API key should decrypt back to original."""
    from config import Config
    with tempfile.TemporaryDirectory() as tmpdir:
        cfg = Config(app_dir=tmpdir)
        cfg.set_api_key("sk-ant-test-key-12345")
        cfg.save()

        cfg2 = Config(app_dir=tmpdir)
        assert cfg2.get_api_key() == "sk-ant-test-key-12345"


def test_app_dir_created_if_missing():
    """Config should create the app directory if it doesn't exist."""
    from config import Config
    with tempfile.TemporaryDirectory() as tmpdir:
        app_dir = os.path.join(tmpdir, "SocialDecoder")
        cfg = Config(app_dir=app_dir)
        cfg.save()
        assert os.path.isdir(app_dir)
        assert os.path.isfile(os.path.join(app_dir, "config.json"))
