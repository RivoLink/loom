from loom.config import config_exists
from loom.spiders.custom import get_custom_spider, list_custom_spiders


def resolve_spider_name(target_name: str) -> str | None:
    """Return the Scrapy spider name for a given target, or None if unknown.

    - If a custom spider is registered for target_name, return its `.name`.
    - Else if a YAML config exists in configs/{target_name}.yaml, return
      "loom" (the generic config-driven spider).
    - Else return None: the API layer turns this into a 404.
    """
    custom_cls = get_custom_spider(target_name)
    if custom_cls is not None:
        return custom_cls.name
    if config_exists(target_name):
        return "loom"
    return None


def resolve_spider_class(spider_name: str) -> type:
    """Return the spider class for a given spider name.

    Used by the subprocess wrapper to instantiate the spider directly
    instead of going through Scrapyd's egg-based discovery.
    """
    from loom.spiders.loom_spider import LoomSpider

    if spider_name == LoomSpider.name:
        return LoomSpider
    for target_name in list_custom_spiders():
        cls = get_custom_spider(target_name)
        if cls is not None and cls.name == spider_name:
            return cls
    raise ValueError(f"unknown spider: {spider_name!r}")
