"""Light e2e: run LoomSpider against quotes.toscrape.com via Scrapy's
CrawlerProcess and check we get at least one item back.

Marked as integration: skipped by default unless LOOM_RUN_NETWORK_TESTS=1.
"""
import json
import os

import pytest


pytestmark = pytest.mark.skipif(
    os.environ.get("LOOM_RUN_NETWORK_TESTS") != "1",
    reason="set LOOM_RUN_NETWORK_TESTS=1 to enable network-bound tests",
)


def test_quotes_to_scrape_yields_items(tmp_path, monkeypatch):
    from scrapy.crawler import CrawlerProcess

    from loom import settings as loom_settings
    from loom.spiders.loom_spider import LoomSpider

    monkeypatch.setenv("LOOM_RESULTS_DIR", str(tmp_path))
    monkeypatch.setattr(loom_settings, "LOOM_RESULTS_DIR", str(tmp_path))

    process = CrawlerProcess(settings={
        "ROBOTSTXT_OBEY": False,
        "LOOM_RESULTS_DIR": str(tmp_path),
        "ITEM_PIPELINES": {"loom.pipelines.JsonFilePipeline": 300},
        "USER_AGENT": "loom-tests/0.1",
        "LOG_LEVEL": "ERROR",
    })
    process.crawl(LoomSpider, target_name="demo_dom_pagination", params='{"page": 1}')
    process.start()

    result_file = next(tmp_path.glob("*.json"))
    items = json.loads(result_file.read_text())
    assert len(items) > 0
    assert any(it.get("author") for it in items)
