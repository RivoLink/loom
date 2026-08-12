import pytest
import yaml

from loom import settings as loom_settings
from loom.resolver import resolve_spider_name


@pytest.fixture
def temp_configs(tmp_path, monkeypatch):
    monkeypatch.setattr(loom_settings, "LOOM_CONFIGS_DIR", str(tmp_path))
    return tmp_path


def test_custom_takes_priority(temp_configs):
    assert resolve_spider_name("demo_custom_spider") == "demo_custom_spider"


def test_yaml_config_falls_back_to_loom(temp_configs):
    cfg = temp_configs / "my_target.yaml"
    with open(cfg, "w", encoding="utf-8") as f:
        yaml.safe_dump({
            "name": "my_target",
            "url": "https://example.com",
            "type": "dom",
            "extract": {"title": {"selector": "h1"}},
        }, f)
    assert resolve_spider_name("my_target") == "loom"


def test_unknown_returns_none(temp_configs):
    assert resolve_spider_name("does_not_exist") is None
