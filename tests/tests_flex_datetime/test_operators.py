from datetime import datetime, timedelta

import pytest

from flexible_datetime import flex_datetime


@pytest.fixture
def sample_dates():
    return {
        "dt1": flex_datetime("2023-01-01"),
        "dt2": flex_datetime("2023-02-01"),
        "dt_with_time1": flex_datetime("2023-01-01T12:00:00"),
        "dt_with_time2": flex_datetime("2023-01-01T14:00:00"),
    }


def test_subtraction_between_flex_datetimes(sample_dates):
    # Test basic subtraction between two flex_datetimes
    delta = sample_dates["dt2"] - sample_dates["dt1"]
    assert isinstance(delta, timedelta)
    assert delta.days == 31

    # Test subtraction with times
    delta = sample_dates["dt_with_time2"] - sample_dates["dt_with_time1"]
    assert isinstance(delta, timedelta)
    assert delta.seconds == 7200  # 2 hours in seconds


def test_subtraction_with_datetime():
    flex_dt = flex_datetime("2023-01-01T12:00:00")
    regular_dt = datetime(2023, 1, 1, 10, 0)

    # Test flex_datetime - datetime
    delta = flex_dt - regular_dt
    assert isinstance(delta, timedelta)
    assert delta.seconds == 7200  # 2 hours difference

    # Test datetime - flex_datetime
    delta = regular_dt - flex_dt
    assert isinstance(delta, timedelta)
    assert delta.seconds == 79200  # 22 hours difference (negative)


def test_subtraction_with_timedelta():
    dt = flex_datetime("2023-01-01T12:00:00")
    delta = timedelta(days=1, hours=2)

    # Test subtraction
    result = dt - delta
    assert isinstance(result, flex_datetime)
    assert result.dt.day == 31
    assert result.dt.hour == 10
    assert result.mask == dt.mask  # Mask should be preserved


def test_addition_with_timedelta():
    dt = flex_datetime("2023-01-01")
    delta = timedelta(days=5)

    # Test regular addition
    result = dt + delta
    assert isinstance(result, flex_datetime)
    assert result.dt.day == 6
    assert result.mask == dt.mask

    # Test reverse addition
    result = delta + dt
    assert isinstance(result, flex_datetime)
    assert result.dt.day == 6
    assert result.mask == dt.mask


def test_operations_with_masked_components():
    # Create flex_datetime with masked hour
    dt1 = flex_datetime("2023-01-01T00:00:00")
    # Manually set the hour mask to True (masked)
    dt1.mask["hour"] = True

    dt2 = flex_datetime("2023-01-02")

    # Subtraction should work with masked components
    delta = dt2 - dt1
    assert isinstance(delta, timedelta)
    assert delta.days == 1


def test_edge_cases():
    dt = flex_datetime("2023-01-01")

    # Test adding zero timedelta
    result = dt + timedelta()
    assert isinstance(result, flex_datetime)
    assert result.dt == dt.dt

    # Test subtracting same datetime
    delta = dt - dt
    assert isinstance(delta, timedelta)
    assert delta.total_seconds() == 0


def test_type_errors():
    dt = flex_datetime("2023-01-01")

    # Test invalid addition
    with pytest.raises(TypeError):
        dt + "invalid"  # type: ignore

    # Test invalid subtraction
    with pytest.raises(TypeError):
        dt - "invalid"  # type: ignore

    with pytest.raises(TypeError):
        "invalid" - dt  # type: ignore


def test_leap_year_operations():
    dt = flex_datetime("2024-02-28")  # Leap year

    # Add one day
    result = dt + timedelta(days=1)
    assert result.dt.day == 29
    assert result.dt.month == 2

    # Add two days
    result = dt + timedelta(days=2)
    assert result.dt.day == 1
    assert result.dt.month == 3


def test_timezone_awareness():
    # Create timezone-aware flex_datetime
    dt1 = flex_datetime("2023-01-01T12:00:00+00:00")
    dt2 = flex_datetime("2023-01-01T14:00:00+02:00")

    # They should represent the same time
    delta = dt2 - dt1
    assert isinstance(delta, timedelta)
    assert delta.total_seconds() == 0


def test_millisecond_precision():
    dt1 = flex_datetime("2023-01-01T12:00:00.123")
    dt2 = flex_datetime("2023-01-01T12:00:00.456")

    delta = dt2 - dt1
    assert isinstance(delta, timedelta)
    assert delta.microseconds == 333000  # 333 milliseconds difference


if __name__ == "__main__":
    pytest.main(["-v", __file__])
