import json
import os
import threading


class JsonFilePipeline:
    """Append each item to results/{job_id}.json as a JSON array.

    Job id is read from the spider attribute `_job_id`, injected by the
    Scheduler when scheduling a crawl. Falls back to `spider.name` so
    standalone `scrapy crawl` invocations still produce a result file.
    """

    def __init__(self, crawler):
        self.crawler = crawler
        self.results_dir = crawler.settings.get("LOOM_RESULTS_DIR")
        self._lock = threading.Lock()
        self._items: list[dict] = []
        self._path: str | None = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def open_spider(self):
        spider = self.crawler.spider
        os.makedirs(self.results_dir, exist_ok=True)
        job_id = getattr(spider, "_job_id", None) or spider.name
        self._path = os.path.join(self.results_dir, f"{job_id}.json")

    def process_item(self, item):
        with self._lock:
            self._items.append(dict(item))
        return item

    def close_spider(self):
        if self._path is None:
            return
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._items, f, ensure_ascii=False, indent=2)
