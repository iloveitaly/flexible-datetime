"""Tests covering previously untested code paths in FlexDateTime."""

import json
from datetime import date, datetime

import arrow
import pytest
from pydantic import BaseModel

from flexible_datetime import FlexDateTime
from flexible_datetime.flexible_datetime import OutputFormat

# ---------- __init__ edge cases ----------


def test_init_none_raises():
    with pytest.raises(ValueError, match="Cannot parse None"):
        FlexDateTime(None)


def test_init_copy_from_flexdatetime():
    original = FlexDateTime.from_str("2024-06-28")
    original.apply_mask(hour=True, minute=True, second=True, millisecond=True)
    copy = FlexDateTime(original)
    assert copy.dt == original.dt
    assert copy.mask == original.mask


def test_init_from_date_object():
    d = date(2024, 3, 15)
    fdt = FlexDateTime(d)
    assert fdt.dt == arrow.get(d)
    assert fdt.dt.year == 2024
    assert fdt.dt.month == 3
    assert fdt.dt.day == 15
    assert fdt.mask == FlexDateTime.binary_to_mask("0001111")


def test_init_no_args():
    fdt = FlexDateTime()
    assert fdt.dt is not None
    assert not any(fdt.mask.values())


# ---------- from_datetime classmethod ----------


def test_from_datetime_classmethod_bug():
    """from_datetime passes dt as a kwarg, which bypasses __init__ positional handling
    and hits the Pydantic super().__init__ path where datetime isn't a valid Arrow type.
    This documents the current broken behavior."""
    dt = datetime(2024, 6, 15, 10, 30, 45)
    with pytest.raises(Exception):
        FlexDateTime.from_datetime(dt)


def test_init_from_datetime_positional():
    """Passing datetime as a positional arg works via the __init__ isinstance chain."""
    dt = datetime(2024, 6, 15, 10, 30, 45)
    fdt = FlexDateTime(dt)
    assert fdt.dt == arrow.get(dt)
    assert fdt.dt.hour == 10
    assert fdt.dt.minute == 30


# ---------- to_datetime ----------


def test_to_datetime():
    fdt = FlexDateTime.from_str("2024-06-28T14:30:45")
    result = fdt.to_datetime()
    assert isinstance(result, datetime)
    assert result.year == 2024
    assert result.month == 6
    assert result.day == 28
    assert result.hour == 14
    assert result.minute == 30
    assert result.second == 45


# ---------- __repr__ ----------


def test_repr_is_json():
    fdt = FlexDateTime.from_str("2024-06-28T14:30:00")
    r = repr(fdt)
    parsed = json.loads(r)
    assert "dt" in parsed
    assert "mask" in parsed


# ---------- model_dump / model_dump_json with OutputFormat.datetime ----------


def test_model_dump_datetime_format():
    fdt = FlexDateTime.from_str("2024-06-28T14:30:00")
    fdt._output_format = OutputFormat.datetime
    fdt.__class__._default_output_format = OutputFormat.datetime
    try:
        d = fdt.model_dump()
        assert "dt" in d
        assert "mask" not in d

        j = fdt.model_dump_json()
        parsed = json.loads(j)
        assert "dt" in parsed
        assert "mask" not in parsed
    finally:
        fdt.__class__._default_output_format = OutputFormat.minimal_datetime


def test_model_dump_default_format():
    fdt = FlexDateTime.from_str("2024-06-28T14:30:00")
    d = fdt.model_dump()
    assert "dt" in d
    assert "mask" in d


# ---------- Comparison with non-FlexDateTime types ----------


def test_eq_non_flexdatetime_returns_false():
    fdt = FlexDateTime.from_str("2024-06-28T14:30:00")
    assert fdt != "2024-06-28T14:30:00"
    assert fdt != 42
    assert fdt != None  # noqa: E711
    assert fdt != datetime(2024, 6, 28, 14, 30)


def test_lt_non_flexdatetime_returns_not_implemented():
    fdt = FlexDateTime.from_str("2024-06-28T14:30:00")
    assert fdt.__lt__("not a FlexDateTime") is NotImplemented
    assert fdt.__le__(42) is NotImplemented
    assert fdt.__gt__(None) is NotImplemented
    assert fdt.__ge__(datetime.now()) is NotImplemented


# ---------- eq() with allow_different_masks ----------


def test_eq_allow_different_masks_same_comparable():
    """allow_different_masks=True skips the mask equality check, but each instance
    still uses its OWN mask for get_comparable_dt(). So this only returns True
    when the comparable datetimes happen to match."""
    fdt1 = FlexDateTime.from_str("2024-06-01")  # mask: 0001111
    fdt2 = FlexDateTime.from_str("2024-06")  # mask: 0011111
    # fdt1 comparable: 2024-06-01 (day=1 unmasked)
    # fdt2 comparable: 2024-06-01 (day=1 because masked defaults to 1)
    assert fdt1.eq(fdt2, allow_different_masks=True)


def test_eq_allow_different_masks_different_comparable():
    """When masks differ and produce different comparable datetimes, returns False."""
    fdt1 = FlexDateTime.from_str("2024-06-28")  # mask: 0001111
    fdt2 = FlexDateTime.from_str("2024-06")  # mask: 0011111
    # fdt1 comparable: 2024-06-28 (day=28 unmasked)
    # fdt2 comparable: 2024-06-01 (day=1 because masked)
    assert not fdt1.eq(fdt2, allow_different_masks=True)


def test_eq_allow_different_masks_false_result():
    fdt1 = FlexDateTime.from_str("2024-06-28T14:30:00")
    fdt2 = FlexDateTime.from_str("2024-07-28T14:30:00")
    assert not fdt1.eq(fdt2, allow_different_masks=True)


def test_eq_allow_different_masks_non_flexdatetime():
    fdt = FlexDateTime.from_str("2024-06-28T14:30:00")
    assert not fdt.eq("not a FlexDateTime", allow_different_masks=True)


# ---------- to_flex ----------


def test_to_flex_structure():
    fdt = FlexDateTime.from_str("2024-06-28")
    result = fdt.to_flex()
    assert isinstance(result, dict)
    assert "dt" in result
    assert "mask" in result
    assert isinstance(result["mask"], str)
    assert len(result["mask"]) == 7


# ---------- to_str ----------


def test_to_str_delegates_to_minimal():
    fdt = FlexDateTime.from_str("2024-06-28")
    assert fdt.to_str() == fdt.to_minimal_datetime()


# ---------- model_validator with various types ----------


def test_model_validator_with_datetime():
    class M(BaseModel):
        fdt: FlexDateTime

    dt = datetime(2024, 6, 28, 14, 30)
    m = M(fdt=dt)
    assert m.fdt.dt == arrow.get(dt)


def test_model_validator_with_arrow():
    class M(BaseModel):
        fdt: FlexDateTime

    a = arrow.get("2024-06-28T14:30:00")
    m = M(fdt=a)
    assert m.fdt.dt == a


def test_model_validator_with_flexdatetime():
    class M(BaseModel):
        fdt: FlexDateTime

    original = FlexDateTime.from_str("2024-06-28")
    m = M(fdt=original)
    assert m.fdt.dt == original.dt


# ---------- from_dict with full components ----------


def test_from_dict_full_components():
    d = {
        "year": 2024,
        "month": 6,
        "day": 28,
        "hour": 14,
        "minute": 30,
        "second": 45,
        "millisecond": 123,
    }
    fdt = FlexDateTime.from_dict(d)
    assert fdt.dt.year == 2024
    assert fdt.dt.month == 6
    assert fdt.dt.day == 28
    assert fdt.dt.hour == 14
    assert fdt.dt.minute == 30
    assert fdt.dt.second == 45
    assert fdt.dt.microsecond == 123000
    assert not any(fdt.mask.values())


if __name__ == "__main__":
    pytest.main(["-v", __file__])
