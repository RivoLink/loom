import pytest

from loom.transforms import apply_transforms, get_transform, register_transform
from loom.transforms.registry import _REGISTRY


def test_strip_builtin():
    assert apply_transforms("  hi  ", "strip") == "hi"


def test_chain_strip_then_to_number():
    assert apply_transforms("  $12.50 ", ["strip", "to_number"]) == 12.5


def test_custom_prefix_resolution():
    assert apply_transforms("hello", "custom:fake_currency") == "CUR::hello"


def test_none_spec_returns_value():
    assert apply_transforms("abc", None) == "abc"


def test_unknown_transform_raises():
    with pytest.raises(KeyError):
        apply_transforms("x", "does_not_exist")


def test_register_duplicate_raises():
    with pytest.raises(ValueError):
        register_transform("strip")(lambda v: v)


def test_to_number_handles_garbage():
    assert apply_transforms("garbage", "to_number") is None
