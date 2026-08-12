from typing import Callable

_REGISTRY: dict[str, Callable] = {}


def register_transform(name: str):
    def decorator(fn: Callable) -> Callable:
        if name in _REGISTRY:
            raise ValueError(f"transform already registered: {name}")
        _REGISTRY[name] = fn
        return fn
    return decorator


def get_transform(name: str) -> Callable:
    key = name[len("custom:"):] if name.startswith("custom:") else name
    if key not in _REGISTRY:
        raise KeyError(f"unknown transform: {name}")
    return _REGISTRY[key]


def apply_transforms(value, spec):
    if spec is None:
        return value
    names = spec if isinstance(spec, list) else [spec]
    for name in names:
        value = get_transform(name)(value)
    return value


def list_transforms() -> list[str]:
    return sorted(_REGISTRY)
