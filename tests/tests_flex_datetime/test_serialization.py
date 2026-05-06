import json
from datetime import date, datetime, timedelta
from unittest.mock import patch

import arrow
import pytest
from dateutil import parser as dateutil_parser
from pydantic import BaseModel

from flexible_datetime import FlexDateTime, flex_datetime


def test_dump_load():
    ft = flex_datetime()
    d = json.dumps(ft.to_json())
    ft2 = flex_datetime.from_json(d)
    assert ft == ft2


def test_dump_load_ymd():
    ft = flex_datetime()
    ft.use_only("year", "month", "day")
    d = json.dumps(ft.to_json())
    ft2 = flex_datetime.from_json(d)
    assert ft == ft2
    assert ft2.mask_str == "0001111"


def test_from_dict():
    d = {"year": 2023, "month": 6, "day": 29}
    ft = flex_datetime(d)
    assert ft.dt == arrow.get("2023-06-29")
    assert ft.mask_str == "0001111"
    assert ft.year == 2023
    assert ft.month == 6
    assert ft.day == 29


def test_from_datetime():
    dt = datetime.now()
    at = arrow.get(dt)
    ft = flex_datetime(dt)

    assert ft.dt == at


def test_from_flexdatetime():
    fdt = FlexDateTime()
    ft = flex_datetime(fdt)

    assert ft.dt == fdt.dt
    assert ft.mask == fdt.mask


def test_from_arrow():
    at = arrow.get()
    ft = flex_datetime(at)

    assert ft.dt == at


def test_dump_load_mode_json():
    ft = flex_datetime()
    d = json.dumps(ft.to_json())
    ft2 = flex_datetime.from_json(d)
    assert ft == ft2


def test_dump_load_mode_json_mask_YYYY():
    ft = flex_datetime()
    ft.use_only("year")
    d = json.dumps(ft.to_json())
    ft2 = flex_datetime.from_json(d)
    assert ft == ft2


def test_from_dict_ymd():
    ft = flex_datetime.from_dict({"year": 2023, "month": 6, "day": 29})
    assert ft.dt == arrow.get("2023-06-29")


def test_from_dict_ym():
    ft = flex_datetime.from_dict({"year": 2023, "month": 6})
    assert ft.dt == arrow.get("2023-06")
    mask = ft.mask_to_binary(ft.mask)
    assert mask == "0011111"


def test_from_flex():
    ft = flex_datetime({"dt": "2023-06-29", "mask": "0001111"})
    assert ft.dt == arrow.get("2023-06-29")
    mask = ft.mask_to_binary(ft.mask)
    assert mask == "0001111"


def test_from_flex_dict_mask():
    ft = flex_datetime({
        "dt": "2023-06-29",
        "mask": {
            "year": False,
            "month": False,
            "day": False,
            "hour": True,
            "minute": True,
            "second": True,
            "millisecond": True,
        },
    })
    assert ft.dt == arrow.get("2023-06-29")
    mask = ft.mask_to_binary(ft.mask)
    assert mask == "0001111"


def test_from_dict_y():
    ft = flex_datetime.from_dict({"year": 2023})
    assert ft.dt == arrow.get("2023")


def test_y():
    ft = flex_datetime({"year": 2023})
    assert ft.dt == arrow.get("2023")


def test_y_str():
    ft = flex_datetime("2023")
    assert ft.dt == arrow.get("2023")


def test_in_class_from_datetime():
    class Test(BaseModel):
        ft: flex_datetime

    js = {"ft": datetime.now()}
    t = Test(**js)  # type: ignore
    assert t.ft.dt == arrow.get(js["ft"])


def test_in_class_from_str():
    class Test(BaseModel):
        ft: flex_datetime

    js = {"ft": "2023-06-29"}
    t = Test(**js)  # type: ignore
    assert t.ft.dt == arrow.get(js["ft"])


def test_in_class_from_components():
    class Test(BaseModel):
        ft: flex_datetime

    js = {"ft": {"year": 2023, "month": 6, "day": 29}}
    t = Test(**js)  # type: ignore
    assert t.ft.dt == arrow.get("2023-06-29")


def test_in_class_from_flexdatetime():
    class Test(BaseModel):
        ft: flex_datetime

    fdt = FlexDateTime("2023-06-29")
    js = {"ft": fdt}
    t = Test(**js)  # type: ignore
    assert t.ft.dt == arrow.get("2023-06-29")


def test_in_class_from_components_dump_load():
    class Test(BaseModel):
        ft: flex_datetime

    js = {"ft": {"year": 2023, "month": 6, "day": 29}}
    t = Test(**js)  # type: ignore
    assert t.ft.dt == arrow.get("2023-06-29")
    d = json.dumps(t.model_dump())
    t2 = Test(**json.loads(d))
    assert t == t2


def test_from_date():
    # Creating a Python date object
    dt = date(2022, 6, 2)
    ft = flex_datetime(dt)

    # Expected output is the corresponding arrow object
    expected_dt = arrow.get(dt)
    assert ft.dt == expected_dt
    assert ft.year == 2022
    assert ft.month == 6
    assert ft.day == 2
    assert ft.mask_str == "0001111"


def test_dump_load_from_date():
    # Creating a Python date object and passing it to flex_datetime
    ft = flex_datetime(date(2022, 6, 2))
    d = json.dumps(ft.to_json())

    # Loading the json back and ensuring the object remains the same
    ft2 = flex_datetime.from_json(d)
    assert ft == ft2
    assert ft2.year == 2022
    assert ft2.month == 6
    assert ft2.day == 2
    assert ft.mask_str == "0001111"


def test_from_dateutil():
    ft = flex_datetime("Aug 28")
    now_ft = flex_datetime()
    assert ft.dt == arrow.get(f"{now_ft.year}-08-28")
    assert ft.mask_str == "0001111"


def test_from_dateutil_with_year():
    ft = flex_datetime("Aug 28, 2024")
    assert ft.dt == arrow.get("2024-08-28")
    assert ft.mask_str == "0001111"


def test_relative_weeks_ago_uses_utc_now_not_calendar_day():
    """'N weeks ago' must be N weeks before now; dateutil fuzzy reads N as day-of-month."""
    fixed = arrow.get("2026-05-06 15:30:00+00:00")
    expected = fixed.datetime - timedelta(weeks=12)

    with patch("flexible_datetime._base.arrow.utcnow", return_value=fixed):
        ft = flex_datetime("12 weeks ago")

    assert ft.to_datetime() == expected
    assert ft.mask_str == "0000000"


def test_from_natural_language():
    reference_time = arrow.get("2024-01-28 10:00:00", tzinfo="local")
    input_str = "next thursday at 2pm"

    parsed_dt = dateutil_parser.parse(input_str, fuzzy=True)
    if parsed_dt.year == 1900:  # Match the code's year fixing logic
        parsed_dt = parsed_dt.replace(year=reference_time.year)

    # Convert to Arrow for comparison
    expected_dt = arrow.get(parsed_dt).to("UTC")

    # Create flex_datetime instance
    ft = flex_datetime(input_str)

    print(f"Reference time: {reference_time}")
    print(f"Parsed datetime: {parsed_dt}")
    print(f"Expected UTC: {expected_dt}")
    print(f"Actual ft.dt: {ft.dt}")

    assert ft.dt == expected_dt
    assert ft.mask_str == "0000000"


if __name__ == "__main__":
    pytest.main(["-v", __file__])
