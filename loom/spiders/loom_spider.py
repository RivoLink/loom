import json

import scrapy
from jsonpath_ng.ext import parse as jsonpath_parse

from loom.config import load_config
from loom.transforms import apply_transforms


class LoomSpider(scrapy.Spider):
    """Generic config-driven spider.

    Reads its config from configs/{target_name}.yaml and interprets the
    extraction rules (DOM or JSON API) declaratively.
    """

    name = "loom"

    def __init__(self, target_name=None, params=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not target_name:
            raise ValueError("LoomSpider requires target_name argument")
        self.target_name = target_name
        self.cfg = load_config(target_name)
        self.params = self._parse_params(params)
        try:
            self.start_url = self.cfg["url"].format(**self.params)
        except KeyError as e:
            raise ValueError(
                f"missing param {e!s} for url template {self.cfg['url']!r}"
            ) from e
        self.headers = self.cfg.get("headers") or {}
        self._pages_seen = 0

    @staticmethod
    def _parse_params(params):
        if params is None:
            return {}
        if isinstance(params, dict):
            return params
        if isinstance(params, str):
            return json.loads(params) if params.strip() else {}
        raise TypeError(f"unsupported params type: {type(params).__name__}")

    start_urls: list[str] = []

    def start_requests(self):
        yield scrapy.Request(self.start_url, headers=self.headers, callback=self.parse)

    async def start(self):
        yield scrapy.Request(self.start_url, headers=self.headers, callback=self.parse)

    def parse(self, response):
        if self.cfg["type"] == "json_api":
            yield from self._parse_json(response)
            return
        yield from self._parse_dom(response)
        self._pages_seen += 1
        next_url = self._next_page(response)
        if next_url:
            yield response.follow(next_url, headers=self.headers, callback=self.parse)

    def _parse_dom(self, response):
        item = {
            field_name: self._extract_dom_value(response, spec)
            for field_name, spec in self.cfg["extract"].items()
        }
        yield item

    @staticmethod
    def _extract_dom_value(response, spec):
        sel = response.css(spec["selector"])
        attribute = spec.get("attribute", "text")
        if attribute == "text":
            raw = [s.css("::text").get() or s.get() for s in sel]
        elif attribute.startswith("attr:"):
            attr = attribute[len("attr:"):]
            raw = [s.attrib.get(attr) for s in sel]
        else:
            raw = [s.get() for s in sel]
        transform = spec.get("transform")
        values = [apply_transforms(v, transform) for v in raw]
        if spec.get("multiple"):
            return values
        return values[0] if values else None

    def _next_page(self, response):
        pagination = self.cfg.get("pagination") or {}
        if pagination.get("type") != "next_link":
            return None
        max_pages = pagination.get("max_pages", 1)
        if self._pages_seen >= max_pages:
            return None
        selector = pagination.get("selector")
        if not selector:
            return None
        return response.css(selector).get()

    def _parse_json(self, response):
        data = json.loads(response.text)
        extract = self.cfg["extract"]
        row = {}
        for field_name, spec in extract.items():
            matches = [m.value for m in jsonpath_parse(spec["path"]).find(data)]
            if spec.get("multiple"):
                row[field_name] = [
                    apply_transforms(v, spec.get("transform")) for v in matches
                ]
            else:
                value = matches[0] if matches else None
                row[field_name] = apply_transforms(value, spec.get("transform"))
        yield row
