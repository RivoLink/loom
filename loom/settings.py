import os

BOT_NAME = "loom"

SPIDER_MODULES = ["loom.spiders"]
NEWSPIDER_MODULE = "loom.spiders"

ROBOTSTXT_OBEY = True

CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 4
DOWNLOAD_DELAY = 0.25

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1
AUTOTHROTTLE_MAX_DELAY = 30
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

RETRY_ENABLED = True
RETRY_TIMES = 2

USER_AGENT = "loom/0.1 (+https://example.invalid/loom)"

ITEM_PIPELINES = {
    "loom.pipelines.JsonFilePipeline": 300,
}

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

LOOM_RESULTS_DIR = os.environ.get(
    "LOOM_RESULTS_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "results"),
)
LOOM_CONFIGS_DIR = os.environ.get(
    "LOOM_CONFIGS_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "configs"),
)
