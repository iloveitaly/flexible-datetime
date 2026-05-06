"""Coverage for English relative phrases (shared by flex_datetime and flex_delta)."""

from datetime import UTC, datetime, timedelta

import pytest
from dateutil.relativedelta import relativedelta

from flexible_datetime.relative_nl import (
    ParsedRelativePhrase,
    RelativeTimeUnit,
    match_relative_english_phrase,
    offset_datetime_for_relative_phrase,
    signed_components_for_relative_phrase,
)

ANCHOR = datetime(2025, 6, 15, 12, 30, 45, 123456, tzinfo=UTC)


@pytest.mark.parametrize(
    ("phrase", "expected"),
    [
        ("7 microseconds ago", ANCHOR - timedelta(microseconds=7)),
        ("7 µs ago", ANCHOR - timedelta(microseconds=7)),
        ("7 milliseconds ago", ANCHOR - timedelta(milliseconds=7)),
        ("7 ms ago", ANCHOR - timedelta(milliseconds=7)),
        ("11 seconds ago", ANCHOR - timedelta(seconds=11)),
        ("11 secs ago", ANCHOR - timedelta(seconds=11)),
        ("5 minutes ago", ANCHOR - timedelta(minutes=5)),
        ("5 mins ago", ANCHOR - timedelta(minutes=5)),
        ("3 hours ago", ANCHOR - timedelta(hours=3)),
        ("3 hrs ago", ANCHOR - timedelta(hours=3)),
        ("9 days ago", ANCHOR - timedelta(days=9)),
        ("2 weeks ago", ANCHOR - timedelta(weeks=2)),
        ("4 months ago", ANCHOR + relativedelta(months=-4)),
        ("6 years ago", ANCHOR + relativedelta(years=-6)),
        ("in 7 microseconds", ANCHOR + timedelta(microseconds=7)),
        ("in 11 seconds", ANCHOR + timedelta(seconds=11)),
        ("in 4 months", ANCHOR + relativedelta(months=4)),
    ],
)
def test_offset_datetime_for_each_unit(phrase: str, expected: datetime) -> None:
    assert offset_datetime_for_relative_phrase(phrase, ANCHOR) == expected


@pytest.mark.parametrize(
    ("phrase", "components"),
    [
        ("7 microseconds ago", {"microseconds": -7}),
        ("7 milliseconds ago", {"microseconds": -7000}),
        ("11 seconds ago", {"seconds": -11}),
        ("5 minutes ago", {"minutes": -5}),
        ("3 hours ago", {"hours": -3}),
        ("9 days ago", {"days": -9}),
        ("2 weeks ago", {"weeks": -2}),
        ("4 months ago", {"months": -4}),
        ("6 years ago", {"years": -6}),
        ("in 4 months", {"months": 4}),
        ("10 ms ago", {"microseconds": -10000}),
        ("10 secs ago", {"seconds": -10}),
        ("10 mins ago", {"minutes": -10}),
        ("10 hrs ago", {"hours": -10}),
    ],
)
def test_signed_components_for_each_unit(phrase: str, components: dict[str, int]) -> None:
    assert signed_components_for_relative_phrase(phrase) == components


def test_try_parse_returns_typed_model() -> None:
    p = ParsedRelativePhrase.try_parse("12 weeks ago")
    assert p is not None
    assert p.sign == -1
    assert p.quantity == 12
    assert p.unit is RelativeTimeUnit.WEEK


def test_try_parse_rejects_zero_quantity() -> None:
    assert ParsedRelativePhrase.try_parse("0 days ago") is None


def test_match_relative_returns_canonical_unit_string() -> None:
    assert match_relative_english_phrase("3 weeks ago") == (-1, 3, "week")


def test_months_are_not_routed_as_minutes() -> None:
    """Regression: 'months' starts with 'min'; must not hit the minute branch."""
    assert offset_datetime_for_relative_phrase("3 months ago", ANCHOR) == ANCHOR + relativedelta(
        months=-3
    )
    assert signed_components_for_relative_phrase("3 months ago") == {"months": -3}
