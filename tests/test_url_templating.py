import pytest
import yaml

from loom import settings as loom_settings
from loom.spiders.loom_spider import LoomSpider


@pytest.fixture
def temp_configs(tmp_path, monkeypatch):
    monkeypatch.setattr(loom_settings, "LOOM_CONFIGS_DIR", str(tmp_path))
    return tmp_path


def _write_dom_config(path, url):
    with open(path, "w", encoding="utf-8") as f:
        yaml.safe_dump(
            {
                "name": "t",
                "url": url,
                "type": "dom",
                "extract": {"title": {"selector": "h1"}},
            },
            f,
        )


def test_format_with_provided_params(temp_configs):
    _write_dom_config(temp_configs / "t.yaml", "https://example.com/p/{id}")
    spider = LoomSpider(target_name="t", params='{"id": 42}')
    assert spider.start_url == "https://example.com/p/42"


def test_missing_param_raises_valueerror(temp_configs):
    _write_dom_config(temp_configs / "t.yaml", "https://example.com/p/{id}")
    with pytest.raises(ValueError, match="missing param"):
        LoomSpider(target_name="t", params="{}")


def test_no_placeholder_is_fine(temp_configs):
    _write_dom_config(temp_configs / "t.yaml", "https://example.com/static")
    spider = LoomSpider(target_name="t", params='{"unused": "x"}')
    assert spider.start_url == "https://example.com/static"


def test_target_name_required():
    with pytest.raises(ValueError, match="target_name"):
        LoomSpider()
