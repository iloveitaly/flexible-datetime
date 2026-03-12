"""Tests covering previously untested code paths in flex_time."""

from datetime import time

import arrow
import pytest

from flexible_datetime import FTOutputFormat, flex_time

# ---------- __init__ edge cases ----------


def test_init_none_raises():
    with pytest.raises(ValueError, match="Cannot parse None"):
        flex_time(None)


def test_init_no_args_raises():
    with pytest.raises(NotImplementedError, match="Unsupported input"):
        flex_time()


def test_init_copy_from_flex_time():
    original = flex_time("14:30:45")
    copy = flex_time(original)
    assert copy.time == original.time
    assert copy.mask == original.mask


def test_init_from_arrow():
    a = arrow.get("2024-06-28T14:30:45")
    ft = flex_time(a)
    assert ft.hour == 14
    assert ft.minute == 30
    assert ft.second == 45
    assert ft.mask["microsecond"] is True


def test_init_from_time_object():
    t = time(9, 15, 30)
    ft = flex_time(t)
    assert ft.time == t
    assert ft.mask["hour"] is False
    assert ft.mask["minute"] is False
    assert ft.mask["second"] is False
    assert ft.mask["microsecond"] is True


def test_init_unsupported_type_raises():
    with pytest.raises(ValueError, match="Unsupported input"):
        flex_time([1, 2, 3])


# ---------- validate classmethod ----------


def test_validate_with_flex_time():
    original = flex_time("14:30")
    result = flex_time.validate(original)
    assert result is original


def test_validate_with_string():
    result = flex_time.validate("14:30")
    assert isinstance(result, flex_time)
    assert result.hour == 14
    assert result.minute == 30


# ---------- to_time ----------


def test_to_time():
    ft = flex_time("14:30:45")
    result = ft.to_time()
    assert isinstance(result, time)
    assert result == time(14, 30, 45)


def test_to_time_loses_mask():
    ft = flex_time({"hour": 14, "minute": 30})
    result = ft.to_time()
    assert isinstance(result, time)
    assert result.second == 0


# ---------- __repr__ ----------


def test_repr_equals_str():
    ft = flex_time("14:30:45")
    assert repr(ft) == str(ft)


def test_repr_short_format():
    ft = flex_time("14:30")
    assert repr(ft) == "14:30"


# ---------- mask_str property ----------


def test_mask_str_property():
    ft = flex_time("14:30:45")
    assert ft.mask_str == ft.mask_to_binary(ft.mask)
    assert isinstance(ft.mask_str, str)


def test_mask_str_with_masked_seconds():
    ft = flex_time("14:30")
    assert ft.mask_str == "0011"


# ---------- set_output_format / output_format setter ----------


def test_set_output_format_with_enum():
    ft = flex_time("14:30:45")
    ft.set_output_format(FTOutputFormat.components)
    assert ft.output_format == FTOutputFormat.components


def test_set_output_format_with_string():
    ft = flex_time("14:30:45")
    ft.set_output_format("components")
    assert ft.output_format == FTOutputFormat.components


def test_output_format_setter_with_string():
    ft = flex_time("14:30:45")
    ft.output_format = "time"
    assert ft.output_format == FTOutputFormat.time


def test_output_format_setter_invalid_string_raises():
    ft = flex_time("14:30:45")
    with pytest.raises(ValueError):
        ft.output_format = "invalid_format"


# ---------- Comparison with non-flex_time types ----------


def test_eq_non_flex_time_returns_false():
    ft = flex_time("14:30:00")
    assert ft != "14:30:00"
    assert ft != 42
    assert ft != None  # noqa: E711
    assert ft != time(14, 30)


def test_lt_non_flex_time_returns_not_implemented():
    ft = flex_time("14:30:00")
    assert ft.__lt__("not a flex_time") is NotImplemented
    assert ft.__le__(42) is NotImplemented
    assert ft.__gt__(None) is NotImplemented
    assert ft.__ge__(time(14, 30)) is NotImplemented


# ---------- Incompatible mask comparison (eq/lt/gt) ----------


def test_eq_incompatible_masks_raises():
    ft1 = flex_time({"hour": 14})
    ft2 = flex_time({"minute": 30})
    with pytest.raises(ValueError, match="incompatible masks"):
        ft1 == ft2


def test_lt_incompatible_masks_raises():
    ft1 = flex_time({"hour": 14})
    ft2 = flex_time({"minute": 30})
    with pytest.raises(ValueError, match="incompatible masks"):
        ft1 < ft2


def test_gt_incompatible_masks_raises():
    ft1 = flex_time({"hour": 14})
    ft2 = flex_time({"minute": 30})
    with pytest.raises(ValueError, match="incompatible masks"):
        ft1 > ft2


def test_le_incompatible_masks_raises():
    ft1 = flex_time({"hour": 14})
    ft2 = flex_time({"minute": 30})
    with pytest.raises(ValueError, match="incompatible masks"):
        ft1 <= ft2


def test_ge_incompatible_masks_raises():
    ft1 = flex_time({"hour": 14})
    ft2 = flex_time({"minute": 30})
    with pytest.raises(ValueError, match="incompatible masks"):
        ft1 >= ft2


# ---------- binary_to_mask padding ----------


def test_binary_to_mask_short_string_padded():
    mask = flex_time.binary_to_mask("00")
    assert mask == {
        "hour": False,
        "minute": False,
        "second": True,
        "microsecond": True,
    }


def test_binary_to_mask_full_string():
    mask = flex_time.binary_to_mask("0101")
    assert mask == {
        "hour": False,
        "minute": True,
        "second": False,
        "microsecond": True,
    }


# ---------- to_str with various output formats ----------


def test_to_str_time_format():
    ft = flex_time("14:30:45")
    result = ft.to_str("time")
    assert result == "14:30:45"


def test_to_str_short_format():
    ft = flex_time("14:30")
    result = ft.to_str("short")
    assert result == "14:30"


def test_to_str_components_format():
    ft = flex_time("14:30:45")
    result = ft.to_str("components")
    assert result == str({"hour": 14, "minute": 30, "second": 45})


def test_to_str_mask_format():
    ft = flex_time("14:30:45")
    result = ft.to_str("mask")
    assert result == str(ft.to_flex())


# ---------- __add__ with non-timedelta ----------


def test_add_non_timedelta_returns_not_implemented():
    ft = flex_time("14:30")
    assert ft.__add__("not a timedelta") is NotImplemented


# ---------- __sub__ with non-flex_time ----------


def test_sub_non_flex_time_returns_not_implemented():
    ft = flex_time("14:30")
    assert ft.__sub__("not a flex_time") is NotImplemented


# ---------- __rsub__ always returns NotImplemented ----------


def test_rsub_returns_not_implemented():
    ft = flex_time("14:30")
    assert ft.__rsub__(time(15, 0)) is NotImplemented


# ---------- __init__ with kwargs (time=, mask=) ----------


def test_init_with_kwargs_time_str_and_mask_str():
    ft = flex_time(time="14:30:45", mask="0001")
    assert ft.hour == 14
    assert ft.minute == 30
    assert ft.second == 45
    assert ft.mask["microsecond"] is True
    assert ft.mask["hour"] is False


def test_init_with_kwargs_time_str_and_mask_dict():
    mask = {"hour": False, "minute": False, "second": True, "microsecond": True}
    ft = flex_time(time="14:30:45", mask=mask)
    assert ft.hour == 14
    assert ft.mask == mask


def test_init_with_kwargs_time_object():
    t = time(14, 30, 45)
    ft = flex_time(time=t)
    assert ft.time == t


def test_init_with_kwargs_invalid_mask_raises():
    with pytest.raises(ValueError, match="Invalid mask"):
        flex_time(time="14:30", mask=12345)


# ---------- to_short_time edge cases ----------


def test_to_short_time_hour_only():
    ft = flex_time({"hour": 14})
    assert ft.to_short_time() == "14"


def test_to_short_time_with_microseconds():
    ft = flex_time(time="14:30:45.123456", mask="0000")
    result = ft.to_short_time()
    assert "123456" in result


if __name__ == "__main__":
    pytest.main(["-v", __file__])
