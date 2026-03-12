"""Tests covering previously untested code paths in flex_datetime."""

from datetime import date, datetime

import arrow
import pytest

from flexible_datetime import FDTOutputFormat, flex_datetime

# ---------- __init__ edge cases ----------


def test_init_none_raises():
    with pytest.raises(ValueError, match="Cannot parse None"):
        flex_datetime(None)


def test_init_unsupported_type_raises():
    with pytest.raises(ValueError, match="Unsupported input"):
        flex_datetime(12345)


def test_init_with_kwargs_dt_and_binary_mask():
    dt = arrow.get("2024-06-28T14:30:00")
    fdt = flex_datetime(dt=dt, mask="0001111")
    assert fdt.dt == dt
    assert fdt.mask_str == "0001111"


def test_init_with_kwargs_dt_and_dict_mask():
    dt = arrow.get("2024-06-28T14:30:00")
    mask = {
        "year": False,
        "month": False,
        "day": False,
        "hour": True,
        "minute": True,
        "second": True,
        "millisecond": True,
    }
    fdt = flex_datetime(dt=dt, mask=mask)
    assert fdt.dt == dt
    assert fdt.mask_str == "0001111"


def test_init_with_kwargs_dt_invalid_mask_raises():
    dt = arrow.get("2024-06-28T14:30:00")
    with pytest.raises(ValueError, match="Invalid mask"):
        flex_datetime(dt=dt, mask=12345)


def test_init_with_kwargs_no_dt_raises():
    with pytest.raises(NotImplementedError, match="Unsupported input"):
        flex_datetime(foo="bar")


# ---------- validate classmethod ----------


def test_validate_with_flex_datetime():
    original = flex_datetime("2024-06-28")
    result = flex_datetime.validate(original)
    assert result is original


def test_validate_with_string():
    result = flex_datetime.validate("2024-06-28")
    assert isinstance(result, flex_datetime)
    assert result.dt == arrow.get("2024-06-28")


# ---------- output_format property/setter ----------


def test_output_format_setter_with_enum():
    fdt = flex_datetime("2024-06-28")
    fdt.output_format = FDTOutputFormat.components
    assert fdt.output_format == FDTOutputFormat.components


def test_output_format_setter_with_string():
    fdt = flex_datetime("2024-06-28")
    fdt.output_format = "components"
    assert fdt.output_format == FDTOutputFormat.components


def test_output_format_setter_invalid_string_raises():
    fdt = flex_datetime("2024-06-28")
    with pytest.raises(ValueError, match="Invalid format"):
        fdt.output_format = "invalid_format"


def test_output_format_setter_invalid_type_raises():
    fdt = flex_datetime("2024-06-28")
    with pytest.raises(ValueError, match="must be an OutputFormat"):
        fdt.output_format = 42


# ---------- set_default_output_format classmethod ----------


def test_set_default_output_format_enum():
    original = flex_datetime._default_output_format
    try:
        flex_datetime.set_default_output_format(FDTOutputFormat.components)
        assert flex_datetime._default_output_format == FDTOutputFormat.components
        fdt = flex_datetime("2024-06-28")
        assert str(fdt) == str(fdt.to_components())
    finally:
        flex_datetime._default_output_format = original


def test_set_default_output_format_string():
    original = flex_datetime._default_output_format
    try:
        flex_datetime.set_default_output_format("datetime")
        assert flex_datetime._default_output_format == FDTOutputFormat.datetime
    finally:
        flex_datetime._default_output_format = original


def test_set_default_output_format_invalid_string_raises():
    with pytest.raises(ValueError, match="Invalid format"):
        flex_datetime.set_default_output_format("bogus")


def test_set_default_output_format_invalid_type_raises():
    with pytest.raises(ValueError, match="must be an OutputFormat"):
        flex_datetime.set_default_output_format(42)


# ---------- to_datetime ----------


def test_to_datetime():
    fdt = flex_datetime("2024-06-28T14:30:45")
    result = fdt.to_datetime()
    assert isinstance(result, datetime)
    assert result.year == 2024
    assert result.month == 6
    assert result.day == 28
    assert result.hour == 14
    assert result.minute == 30
    assert result.second == 45


# ---------- to_mask (alias for to_flex) ----------


def test_to_mask_equals_to_flex():
    fdt = flex_datetime("2024-06-28")
    assert fdt.to_mask() == fdt.to_flex()


# ---------- __json__ ----------


def test_json_dunder():
    fdt = flex_datetime("2024-06-28")
    assert fdt.__json__() == fdt.to_json()


# ---------- eq() with allow_different_masks ----------


def test_eq_allow_different_masks_same_comparable():
    """allow_different_masks=True skips the mask equality check, but each instance
    still uses its OWN mask for get_comparable_dt(). Returns True only when
    comparable datetimes happen to match."""
    fdt1 = flex_datetime("2024-06-01")  # mask: 0001111
    fdt2 = flex_datetime("2024-06")  # mask: 0011111
    assert fdt1.eq(fdt2, allow_different_masks=True)


def test_eq_allow_different_masks_different_comparable():
    fdt1 = flex_datetime("2024-06-28")  # mask: 0001111
    fdt2 = flex_datetime("2024-06")  # mask: 0011111
    assert not fdt1.eq(fdt2, allow_different_masks=True)


def test_eq_allow_different_masks_not_equal():
    fdt1 = flex_datetime("2024-06-28T14:30:00")
    fdt2 = flex_datetime("2024-07-28T14:30:00")
    assert not fdt1.eq(fdt2, allow_different_masks=True)


def test_eq_allow_different_masks_non_flex_datetime():
    fdt = flex_datetime("2024-06-28")
    assert not fdt.eq("not a flex_datetime", allow_different_masks=True)


# ---------- Mask manipulation methods ----------


def test_apply_mask():
    fdt = flex_datetime("2024-06-28T14:30:00")
    assert fdt.mask["year"] is False
    fdt.apply_mask(year=True, month=True)
    assert fdt.mask["year"] is True
    assert fdt.mask["month"] is True
    assert fdt.mask["day"] is False


def test_clear_mask():
    fdt = flex_datetime("2024-06-28")
    assert fdt.mask["hour"] is True
    fdt.clear_mask()
    assert all(v is False for v in fdt.mask.values())


def test_toggle_mask():
    fdt = flex_datetime("2024-06-28T14:30:00")
    assert fdt.mask["year"] is False
    assert fdt.mask["hour"] is False
    fdt.toggle_mask(year=True, hour=True)
    assert fdt.mask["year"] is True
    assert fdt.mask["hour"] is True
    fdt.toggle_mask(year=True)
    assert fdt.mask["year"] is False


# ---------- mask_str property ----------


def test_mask_str_property():
    fdt = flex_datetime("2024-06-28")
    assert fdt.mask_str == fdt.mask_to_binary(fdt.mask)
    assert isinstance(fdt.mask_str, str)
    assert len(fdt.mask_str) == 7


# ---------- millisecond / microsecond properties ----------


def test_millisecond_property():
    fdt = flex_datetime("2024-06-28T14:30:45.123")
    assert fdt.millisecond == 123


def test_microsecond_property():
    fdt = flex_datetime("2024-06-28T14:30:45.123456")
    assert fdt.microsecond == 123456


# ---------- from_str with explicit input_fmt ----------


def test_from_str_with_explicit_format():
    fdt = flex_datetime.from_str("06-28-2024", "MM-DD-YYYY")
    assert fdt.dt == arrow.get("2024-06-28")
    assert fdt.year == 2024
    assert fdt.month == 6
    assert fdt.day == 28


# ---------- from_datetime classmethod ----------


def test_from_datetime_classmethod():
    dt = datetime(2024, 6, 15, 10, 30, 45)
    fdt = flex_datetime.from_datetime(dt)
    assert fdt.dt == arrow.get(dt)
    assert fdt.hour == 10


def test_from_datetime_classmethod_with_date():
    d = date(2024, 6, 15)
    fdt = flex_datetime.from_datetime(d)
    assert fdt.dt == arrow.get(d)
    assert fdt.year == 2024


# ---------- Comparison with non-flex_datetime types ----------


def test_eq_non_flex_datetime_returns_false():
    fdt = flex_datetime("2024-06-28T14:30:00")
    assert fdt != "2024-06-28T14:30:00"
    assert fdt != 42
    assert fdt != None  # noqa: E711
    assert fdt != datetime(2024, 6, 28, 14, 30)


def test_lt_non_flex_datetime_returns_not_implemented():
    fdt = flex_datetime("2024-06-28T14:30:00")
    assert fdt.__lt__("not a flex_datetime") is NotImplemented
    assert fdt.__le__(42) is NotImplemented
    assert fdt.__gt__(None) is NotImplemented
    assert fdt.__ge__(datetime.now()) is NotImplemented


# ---------- to_short_datetime with timezone ----------


def test_to_short_datetime_no_timezone_in_default_output():
    """The timezone handling code in to_short_datetime is dead code — _dt_formats
    has no 'tzinfo' entry, so %z is never replaced and gets stripped by regex cleanup.
    This test documents that timezone is NOT included in short output."""
    fdt = flex_datetime("2024-06-28T14:30:00+05:30")
    fdt.clear_mask()
    result = fdt.to_short_datetime()
    assert "2024" in result
    assert "14" in result
    assert "+05:30" not in result


def test_to_short_datetime_all_unmasked():
    fdt = flex_datetime("2024-06-28T14:30:45.123456+00:00")
    fdt.clear_mask()
    result = fdt.to_short_datetime()
    assert result.startswith("2024-06-28")
    assert "14:30:45" in result


# ---------- __str__ / __repr__ ----------


def test_repr_equals_str():
    fdt = flex_datetime("2024-06-28")
    assert repr(fdt) == str(fdt)


# ---------- to_str with various output formats ----------


def test_to_str_mask_format():
    fdt = flex_datetime("2024-06-28")
    result = fdt.to_str("mask")
    assert result == str(fdt.to_flex())


def test_to_str_components_format():
    fdt = flex_datetime("2024-06-28")
    result = fdt.to_str("components")
    assert result == str(fdt.to_components())


def test_to_str_datetime_format():
    fdt = flex_datetime("2024-06-28T14:30:00")
    fdt.clear_mask()
    result = fdt.to_str("datetime")
    assert result == str(fdt.dt)


if __name__ == "__main__":
    pytest.main(["-v", __file__])
