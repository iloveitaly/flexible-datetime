import arrow
import pytest

from flexible_datetime import FlexDateTime


def test_from_str_valid():
    fdt = FlexDateTime.from_str("2024-06-28T14:30:00")
    assert fdt.dt == arrow.get("2024-06-28T14:30:00")


def test_from_str_invalid():
    with pytest.raises(ValueError):
        FlexDateTime.from_str("invalid date")


def test_str_with_mask():
    fdt = FlexDateTime.from_str("2024-06-28T14:30:00")
    fdt.apply_mask(year=True, month=True)
    assert str(fdt) == "28 14:30:00"


def test_str_no_mask():
    fdt = FlexDateTime.from_str("2024-06-28T14:30:00")
    assert str(fdt) == "2024-06-28 14:30:00"


def test_str_invalid_datetime():
    with pytest.raises(ValueError):
        FlexDateTime.from_str("invalid date")


def test_year_only():
    fdt = FlexDateTime.from_str("2024")
    assert fdt.dt == arrow.get("2024")
    assert str(fdt) == "2024"


def test_year_month():
    fdt = FlexDateTime.from_str("2024-06")
    assert fdt.dt == arrow.get("2024-06")
    assert str(fdt) == "2024-06"


def test_year_month_day():
    fdt = FlexDateTime.from_str("2024-06-28")
    assert fdt.dt == arrow.get("2024-06-28")
    assert str(fdt) == "2024-06-28"


def test_year_month_day_compact():
    fdt = FlexDateTime.from_str("20240628")
    assert fdt.dt == arrow.get("20240628", "YYYYMMDD")
    assert str(fdt) == "2024-06-28"


def test_year_month_compact():
    fdt = FlexDateTime.from_str("202406", input_fmt="YYYYMM")
    assert fdt.dt == arrow.get("202406", "YYYYMM")
    assert str(fdt) == "2024-06"


def test_year_month_compact_output_fmt():
    fdt = FlexDateTime.from_str("202406", input_fmt="YYYYMM")
    assert fdt.dt == arrow.get("202406", "YYYYMM")
    assert fdt.to_minimal_datetime(output_fmt="YYYYMM") == "202406"


def test_equality():
    fdt1 = FlexDateTime.from_str("2024-06-28T14:30:00")
    fdt2 = FlexDateTime.from_str("2024-06-28T14:30:00")
    assert fdt1 == fdt2


def test_equality_with_mask():
    fdt1 = FlexDateTime.from_str("2024-06-28T14:30:00")
    fdt1.apply_mask(year=True)
    fdt2 = FlexDateTime.from_str("2022-06-28T14:30:00")
    fdt2.apply_mask(year=True)
    assert fdt1 == fdt2


def test_equality_year_month_day():
    fdt1 = FlexDateTime.from_str("2024-06-28")
    fdt2 = FlexDateTime.from_str("2024-06-28")
    assert fdt1 == fdt2


def test_equality_different_masks():
    fdt1 = FlexDateTime.from_str("2024-06-28")
    fdt2 = FlexDateTime.from_str("2024-06")
    with pytest.raises(ValueError):
        assert fdt1 == fdt2


def test_equality_mask_day():
    fdt1 = FlexDateTime.from_str("2024-06-28")
    fdt1.apply_mask(day=True)
    fdt2 = FlexDateTime.from_str("2024-06")
    assert fdt1.eq(fdt2, allow_different_masks=True)


def test_alternate_input_fmt():
    fdt = FlexDateTime.from_str("06-28-2023", "MM-DD-YYYY")
    assert fdt.dt == arrow.get("2023-06-28")


if __name__ == "__main__":
    pytest.main([__file__])
