_REGISTRY: dict[str, type] = {}


def register_custom_spider(target_name: str, spider_cls: type) -> None:
    if target_name in _REGISTRY:
        raise ValueError(f"custom spider already registered: {target_name}")
    _REGISTRY[target_name] = spider_cls


def get_custom_spider(target_name: str) -> type | None:
    return _REGISTRY.get(target_name)


def list_custom_spiders() -> list[str]:
    return sorted(_REGISTRY)


from . import demo_custom_spider  # noqa: E402,F401 (triggers registration)
