from datetime import datetime

import arrow
import pytest
from pydantic import BaseModel

from flexible_datetime import FlexDateTime


def test_dump_load():
    fdt = FlexDateTime()
    d = fdt.model_dump()
    fdt2 = FlexDateTime(**d)
    assert fdt == fdt2


def test_from_datetime():
    dt = datetime.now()
    at = arrow.get(dt)
    fdt = FlexDateTime(dt)

    assert fdt.dt == at


def test_from_arrow():
    at = arrow.get()
    fdt = FlexDateTime(at)

    assert fdt.dt == at


def test_dump_load_mode_json():
    fdt = FlexDateTime()
    d = fdt.model_dump(mode="json")
    fdt2 = FlexDateTime(**d)
    assert fdt == fdt2


def test_dump_load_mode_json_mask_YYYY():
    fdt = FlexDateTime()
    fdt.use_only("year")
    d = fdt.model_dump(mode="json")
    fdt2 = FlexDateTime(**d)
    assert fdt == fdt2


def test_from_dict_ymd():
    fdt = FlexDateTime.from_dict({"year": 2023, "month": 6, "day": 29})
    assert fdt.dt == arrow.get("2023-06-29")


def test_from_dict_ym():
    fdt = FlexDateTime.from_dict({"year": 2023, "month": 6})
    assert fdt.dt == arrow.get("2023-06")
    mask = fdt.mask_to_binary(fdt.mask)
    assert mask == "0011111"


def test_from_dict_y():
    fdt = FlexDateTime.from_dict({"year": 2023})
    assert fdt.dt == arrow.get("2023")


def test_y():
    fdt = FlexDateTime({"year": 2023})
    assert fdt.dt == arrow.get("2023")


def test_y_str():
    fdt = FlexDateTime("2023")
    assert fdt.dt == arrow.get("2023")


def test_in_class_from_datetime():
    class Test(BaseModel):
        fdt: FlexDateTime

    js = {"fdt": datetime.now()}
    t = Test(**js)  # type: ignore
    assert t.fdt.dt == arrow.get(js["fdt"])


def test_in_class_from_str():
    class Test(BaseModel):
        fdt: FlexDateTime

    js = {"fdt": "2023-06-29"}
    t = Test(**js)  # type: ignore
    assert t.fdt.dt == arrow.get(js["fdt"])


if __name__ == "__main__":
    pytest.main([__file__])
