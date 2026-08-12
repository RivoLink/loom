import os

import pytest
import yaml

from loom import settings as loom_settings
from loom.config import load_config


@pytest.fixture
def temp_configs(tmp_path, monkeypatch):
    monkeypatch.setattr(loom_settings, "LOOM_CONFIGS_DIR", str(tmp_path))
    return tmp_path


def _write(path, content):
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(content, f)


def test_load_valid_dom_config(temp_configs):
    _write(temp_configs / "ok.yaml", {
        "name": "ok",
        "url": "https://example.com",
        "type": "dom",
        "extract": {"title": {"selector": "h1"}},
    })
    cfg = load_config("ok")
    assert cfg["type"] == "dom"
    assert cfg["extract"]["title"]["selector"] == "h1"


def test_load_valid_json_api_config(temp_configs):
    _write(temp_configs / "api.yaml", {
        "name": "api",
        "url": "https://api.example.com",
        "type": "json_api",
        "extract": {"id": {"path": "$.id"}},
    })
    cfg = load_config("api")
    assert cfg["type"] == "json_api"


def test_missing_file_raises(temp_configs):
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent")


def test_invalid_type_raises(temp_configs):
    _write(temp_configs / "bad.yaml", {
        "name": "bad",
        "url": "https://example.com",
        "type": "unknown",
        "extract": {},
    })
    with pytest.raises(ValueError):
        load_config("bad")


def test_extra_field_rejected(temp_configs):
    _write(temp_configs / "extra.yaml", {
        "name": "extra",
        "url": "https://example.com",
        "type": "dom",
        "extract": {"title": {"selector": "h1"}},
        "unexpected_field": True,
    })
    with pytest.raises(Exception):
        load_config("extra")
