"""Config schema validation using dataclasses.

Kept dependency-free so the config loader can run without pydantic.
The API layer (loom/api/models.py) still uses pydantic: it's only
imported when running the API, not during spider/config tests.
"""
from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any


TransformSpec = str | list[str] | None
_ALLOWED_PAGINATION_TYPES = {"next_link", "none"}


class SchemaError(ValueError):
    pass


@dataclass
class DomField:
    selector: str
    attribute: str = "text"
    multiple: bool = False
    transform: TransformSpec = None


@dataclass
class JsonField:
    path: str
    multiple: bool = False
    transform: TransformSpec = None


@dataclass
class Pagination:
    type: str = "none"
    selector: str | None = None
    max_pages: int = 1


@dataclass
class DomConfig:
    name: str
    url: str
    type: str
    extract: dict[str, DomField]
    headers: dict[str, str] = field(default_factory=dict)
    pagination: Pagination = field(default_factory=Pagination)


@dataclass
class JsonApiConfig:
    name: str
    url: str
    type: str
    extract: dict[str, JsonField]
    headers: dict[str, str] = field(default_factory=dict)


def _check_extra(raw: dict, dc_cls, where: str) -> None:
    allowed = {f.name for f in fields(dc_cls)}
    extra = set(raw) - allowed
    if extra:
        raise SchemaError(f"{where}: unexpected fields {sorted(extra)}")


def _check_transform(value: Any, where: str) -> None:
    if value is None:
        return
    if isinstance(value, str):
        return
    if isinstance(value, list) and all(isinstance(v, str) for v in value):
        return
    raise SchemaError(f"{where}.transform: must be str, list[str] or null")


def _build_dom_field(name: str, raw: dict) -> DomField:
    if not isinstance(raw, dict):
        raise SchemaError(f"extract.{name}: must be a mapping")
    _check_extra(raw, DomField, f"extract.{name}")
    if "selector" not in raw:
        raise SchemaError(f"extract.{name}: missing 'selector'")
    _check_transform(raw.get("transform"), f"extract.{name}")
    return DomField(
        selector=raw["selector"],
        attribute=raw.get("attribute", "text"),
        multiple=raw.get("multiple", False),
        transform=raw.get("transform"),
    )


def _build_json_field(name: str, raw: dict) -> JsonField:
    if not isinstance(raw, dict):
        raise SchemaError(f"extract.{name}: must be a mapping")
    _check_extra(raw, JsonField, f"extract.{name}")
    if "path" not in raw:
        raise SchemaError(f"extract.{name}: missing 'path'")
    _check_transform(raw.get("transform"), f"extract.{name}")
    return JsonField(
        path=raw["path"],
        multiple=raw.get("multiple", False),
        transform=raw.get("transform"),
    )


def _build_pagination(raw: dict | None) -> Pagination:
    if raw is None:
        return Pagination()
    if not isinstance(raw, dict):
        raise SchemaError("pagination: must be a mapping")
    _check_extra(raw, Pagination, "pagination")
    ptype = raw.get("type", "none")
    if ptype not in _ALLOWED_PAGINATION_TYPES:
        raise SchemaError(
            f"pagination.type: {ptype!r} not in {sorted(_ALLOWED_PAGINATION_TYPES)}"
        )
    return Pagination(
        type=ptype,
        selector=raw.get("selector"),
        max_pages=raw.get("max_pages", 1),
    )


def _dump(obj: Any) -> Any:
    if is_dataclass(obj):
        return {f.name: _dump(getattr(obj, f.name)) for f in fields(obj)}
    if isinstance(obj, dict):
        return {k: _dump(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_dump(v) for v in obj]
    return obj


def _validate_dom(raw: dict) -> dict:
    _check_extra(raw, DomConfig, "<root>")
    for key in ("name", "url", "type", "extract"):
        if key not in raw:
            raise SchemaError(f"missing required field: {key}")
    extract = raw["extract"]
    if not isinstance(extract, dict):
        raise SchemaError("extract: must be a mapping")
    cfg = DomConfig(
        name=raw["name"],
        url=raw["url"],
        type=raw["type"],
        headers=raw.get("headers", {}) or {},
        pagination=_build_pagination(raw.get("pagination")),
        extract={name: _build_dom_field(name, spec) for name, spec in extract.items()},
    )
    return _dump(cfg)


def _validate_json_api(raw: dict) -> dict:
    _check_extra(raw, JsonApiConfig, "<root>")
    for key in ("name", "url", "type", "extract"):
        if key not in raw:
            raise SchemaError(f"missing required field: {key}")
    extract = raw["extract"]
    if not isinstance(extract, dict):
        raise SchemaError("extract: must be a mapping")
    cfg = JsonApiConfig(
        name=raw["name"],
        url=raw["url"],
        type=raw["type"],
        headers=raw.get("headers", {}) or {},
        extract={name: _build_json_field(name, spec) for name, spec in extract.items()},
    )
    return _dump(cfg)


def validate(raw: dict) -> dict:
    t = raw.get("type")
    if t == "dom":
        return _validate_dom(raw)
    if t == "json_api":
        return _validate_json_api(raw)
    raise SchemaError(f"unknown config type: {t!r} (expected 'dom' or 'json_api')")
