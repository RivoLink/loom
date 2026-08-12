import json

import scrapy

from loom.spiders.custom import register_custom_spider


class DemoCustomSpider(scrapy.Spider):
    """Demonstrates the custom-spider path of the resolver.

    Same target as configs/demo_dom_pagination.yaml but parses with hardcoded
    selectors instead of going through the YAML interpreter. Registered as
    target_name="demo_custom_spider" so it is distinct from the YAML target.
    """

    name = "demo_custom_spider"

    def __init__(self, target_name=None, params=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_name = target_name or "demo_custom_spider"
        self.params = self._parse_params(params)

    @staticmethod
    def _parse_params(params):
        if params is None:
            return {}
        if isinstance(params, dict):
            return params
        if isinstance(params, str):
            return json.loads(params) if params.strip() else {}
        return {}

    start_urls: list[str] = []

    def start_requests(self):
        yield scrapy.Request("https://quotes.toscrape.com/", callback=self.parse)

    async def start(self):
        yield scrapy.Request("https://quotes.toscrape.com/", callback=self.parse)

    def parse(self, response):
        for quote in response.css("div.quote"):
            yield {
                "text": (quote.css("span.text::text").get() or "").strip(),
                "author": (quote.css("small.author::text").get() or "").strip(),
                "tags": quote.css("div.tags a.tag::text").getall(),
                "source": "custom_spider",
            }


register_custom_spider("demo_custom_spider", DemoCustomSpider)
