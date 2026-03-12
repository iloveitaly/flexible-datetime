import pytest

from flexible_datetime.time_utils import infer_time_format


def test_format_YYYY():
    assert infer_time_format("2023") == "YYYY"


def test_format_YYYYMM():
    assert infer_time_format("202306") == "YYYYMM"


def test_format_YYYY_MM():
    assert infer_time_format("2023-06") == "YYYY-MM"


def test_format_YYYYMMDD():
    assert infer_time_format("20230629") == "YYYYMMDD"


def test_format_YYYY_MM_DD():
    assert infer_time_format("2023-06-29") == "YYYY-MM-DD"


def test_format_YYYY_MM_DDTHH():
    assert infer_time_format("2023-06-29T14") == "YYYY-MM-DDTHH"


def test_format_YYYYMMDDTHHmm():
    assert infer_time_format("20230629T1455") == "YYYYMMDDTHHmm"


def test_format_YYYY_MM_DDTHH_mm():
    assert infer_time_format("2023-06-29T14:55") == "YYYY-MM-DDTHH:mm"


def test_format_YYYYMMDDTHHmmss():
    assert infer_time_format("20230629T145530") == "YYYYMMDDTHHmmss"


def test_format_YYYY_MM_DDTHH_mm_ss():
    assert infer_time_format("2023-06-29T14:55:30") == "YYYY-MM-DDTHH:mm:ss"


def test_format_YYYYMMDDTHHmmssSSS():
    assert infer_time_format("20230629T145530.123") == "YYYYMMDDTHHmmssSSS"


def test_format_YYYY_MM_DDTHH_mm_ssSSS():
    assert infer_time_format("2023-06-29T14:55:30.123") == "YYYY-MM-DDTHH:mm:ssSSS"


def test_format_YYYYMMDDTHHmmssSSSSSS():
    assert infer_time_format("20230629T145530.123456") == "YYYYMMDDTHHmmssSSSSSS"


def test_format_YYYY_MM_DDTHH_mm_ssSSSSSS():
    assert infer_time_format("2023-06-29T14:55:30.123456") == "YYYY-MM-DDTHH:mm:ssSSSSSS"


def test_format_YYYYMMDDTHHmmssSSSSSSZZ():
    assert infer_time_format("20230629T145530.123456Z") == "YYYYMMDDTHHmmssSSSSSSZZ"


def test_format_YYYY_MM_DDTHH_mm_ssSSSSSSZZ():
    assert infer_time_format("2023-06-29T14:55:30.123456+00:00") == "YYYY-MM-DDTHH:mm:ssSSSSSSZZ"


def test_invalid_format():
    with pytest.raises(ValueError):
        infer_time_format("invalid_date")


# Run the tests
if __name__ == "__main__":
    pytest.main(["-v", __file__])
