import os

import yaml

from . import schema


def _configs_dir() -> str:
    from loom import settings as loom_settings

    return loom_settings.LOOM_CONFIGS_DIR


def config_path(target_name: str) -> str:
    return os.path.join(_configs_dir(), f"{target_name}.yaml")


def config_exists(target_name: str) -> bool:
    return os.path.isfile(config_path(target_name))


def load_config(target_name: str) -> dict:
    path = config_path(target_name)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"no config for target_name={target_name!r} at {path}")
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    if not isinstance(raw, dict):
        raise ValueError(f"config {path} must be a YAML mapping")
    return schema.validate(raw)


def list_configs() -> list[str]:
    d = _configs_dir()
    if not os.path.isdir(d):
        return []
    return sorted(f[: -len(".yaml")] for f in os.listdir(d) if f.endswith(".yaml"))
