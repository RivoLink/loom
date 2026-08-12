import re

from .registry import register_transform


@register_transform("strip")
def _strip(v):
    return v.strip() if isinstance(v, str) else v


@register_transform("lower")
def _lower(v):
    return v.lower() if isinstance(v, str) else v


@register_transform("upper")
def _upper(v):
    return v.upper() if isinstance(v, str) else v


@register_transform("to_number")
def _to_number(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    cleaned = re.sub(r"[^\d.\-]", "", str(v))
    return float(cleaned) if cleaned not in ("", "-", ".", "-.") else None


@register_transform("to_int")
def _to_int(v):
    n = _to_number(v)
    return int(n) if n is not None else None


@register_transform("fake_currency")
def _fake_currency(v):
    """Demo hook: prefixes a string with a fake currency marker.

    Used by configs/demo_dom_transform.yaml to demonstrate the named-hook mechanism.
    """
    if v is None:
        return None
    return f"CUR::{str(v).strip()}"
