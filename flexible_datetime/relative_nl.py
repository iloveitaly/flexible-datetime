"""English relative time phrases (e.g. "12 weeks ago").

dateutil fuzzy parsing mis-reads these as literal calendar dates; flex_delta's compact
parser rejects the trailing "ago". Phrases are structured with regex, then validated and
interpreted via :class:`ParsedRelativePhrase` (Pydantic). Units are recognized with an
ordered list of regex fragments (longest / most specific first—e.g. ``months?`` before
``minutes?``—so we never rely on fragile string prefixes).
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Final, Literal

from dateutil.relativedelta import relativedelta
from pydantic import BaseModel, ConfigDict, Field, ValidationError

__all__ = [
    "ParsedRelativePhrase",
    "RelativeTimeUnit",
    "match_relative_english_phrase",
    "offset_datetime_for_relative_phrase",
    "signed_components_for_relative_phrase",
]


class RelativeTimeUnit(StrEnum):
    """Canonical duration unit for relative English phrases (singular name)."""

    MICROSECOND = "microsecond"
    MILLISECOND = "millisecond"
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


# (pattern, canonical unit). Order matters: same as ``patternA|patternB|…`` left-to-right.
_RELATIVE_UNIT_SPECS: Final[tuple[tuple[str, RelativeTimeUnit], ...]] = (
    (r"microseconds?", RelativeTimeUnit.MICROSECOND),
    (r"µs", RelativeTimeUnit.MICROSECOND),
    (r"milliseconds?", RelativeTimeUnit.MILLISECOND),
    (r"ms", RelativeTimeUnit.MILLISECOND),
    (r"seconds?", RelativeTimeUnit.SECOND),
    (r"secs?", RelativeTimeUnit.SECOND),
    (r"months?", RelativeTimeUnit.MONTH),
    (r"minutes?", RelativeTimeUnit.MINUTE),
    (r"mins?", RelativeTimeUnit.MINUTE),
    (r"years?", RelativeTimeUnit.YEAR),
    (r"hours?", RelativeTimeUnit.HOUR),
    (r"hrs?", RelativeTimeUnit.HOUR),
    (r"days?", RelativeTimeUnit.DAY),
    (r"weeks?", RelativeTimeUnit.WEEK),
)

_REL_UNIT_PATTERN = "|".join(pat for pat, _ in _RELATIVE_UNIT_SPECS)


def _canonical_unit(token: str) -> RelativeTimeUnit | None:
    """Map a captured unit token to :class:`RelativeTimeUnit` using the same rules as the lexer."""
    for pat, unit in _RELATIVE_UNIT_SPECS:
        if re.fullmatch(pat, token, re.IGNORECASE):
            return unit
    return None


_REL_AGO_RE = re.compile(
    rf"^\s*(?P<n>a|an|\d+)\s+(?P<unit>{_REL_UNIT_PATTERN})\s+ago\s*$",
    re.IGNORECASE,
)
_REL_FROM_NOW_RE = re.compile(
    rf"^\s*(?P<n>a|an|\d+)\s+(?P<unit>{_REL_UNIT_PATTERN})\s+from\s+now\s*$",
    re.IGNORECASE,
)
_REL_IN_RE = re.compile(
    rf"^\s*in\s+(?P<n>a|an|\d+)\s+(?P<unit>{_REL_UNIT_PATTERN})\s*$",
    re.IGNORECASE,
)


def _quantity_from_lexer(n_group: str) -> int:
    lowered = n_group.lower()
    if lowered in ("a", "an"):
        return 1
    return int(n_group)


class ParsedRelativePhrase(BaseModel):
    """Structured parse of a relative English phrase."""

    model_config = ConfigDict(frozen=True)

    sign: Literal[-1, 1]
    quantity: int = Field(gt=0)
    unit: RelativeTimeUnit

    @classmethod
    def try_parse(cls, text: str) -> ParsedRelativePhrase | None:
        """Parse *text* or return ``None`` if it is not a supported phrase."""
        t = text.strip()
        if not t:
            return None

        sign: Literal[-1, 1] | None = None
        raw_n: str | None = None
        raw_unit: str | None = None

        if m := _REL_AGO_RE.fullmatch(t):
            sign, raw_n, raw_unit = -1, m.group("n"), m.group("unit")
        elif m := _REL_FROM_NOW_RE.fullmatch(t):
            sign, raw_n, raw_unit = 1, m.group("n"), m.group("unit")
        elif m := _REL_IN_RE.fullmatch(t):
            sign, raw_n, raw_unit = 1, m.group("n"), m.group("unit")

        if sign is None or raw_n is None or raw_unit is None:
            return None

        quantity = _quantity_from_lexer(raw_n)
        unit = _canonical_unit(raw_unit)
        if unit is None:
            return None

        try:
            return cls(sign=sign, quantity=quantity, unit=unit)
        except ValidationError:
            return None

    def signed_amount(self) -> int:
        """``sign * quantity`` (negative for \"… ago\")."""
        return self.sign * self.quantity

    def offset_from(self, anchor: datetime) -> datetime:
        """Shift *anchor* by this phrase (fixed units use :class:`~datetime.timedelta`)."""
        s = self.signed_amount()
        match self.unit:
            case RelativeTimeUnit.MICROSECOND:
                return anchor + timedelta(microseconds=s)
            case RelativeTimeUnit.MILLISECOND:
                return anchor + timedelta(milliseconds=s)
            case RelativeTimeUnit.SECOND:
                return anchor + timedelta(seconds=s)
            case RelativeTimeUnit.MINUTE:
                return anchor + timedelta(minutes=s)
            case RelativeTimeUnit.HOUR:
                return anchor + timedelta(hours=s)
            case RelativeTimeUnit.DAY:
                return anchor + timedelta(days=s)
            case RelativeTimeUnit.WEEK:
                return anchor + timedelta(weeks=s)
            case RelativeTimeUnit.MONTH:
                return anchor + relativedelta(months=s)
            case RelativeTimeUnit.YEAR:
                return anchor + relativedelta(years=s)

    def signed_flex_delta_components(self) -> dict[str, int]:
        """Components compatible with :class:`~flexible_datetime.flex_delta.flex_delta`."""
        s = self.signed_amount()
        match self.unit:
            case RelativeTimeUnit.MICROSECOND:
                return {"microseconds": s}
            case RelativeTimeUnit.MILLISECOND:
                return {"microseconds": s * 1000}
            case RelativeTimeUnit.SECOND:
                return {"seconds": s}
            case RelativeTimeUnit.MINUTE:
                return {"minutes": s}
            case RelativeTimeUnit.HOUR:
                return {"hours": s}
            case RelativeTimeUnit.DAY:
                return {"days": s}
            case RelativeTimeUnit.WEEK:
                return {"weeks": s}
            case RelativeTimeUnit.MONTH:
                return {"months": s}
            case RelativeTimeUnit.YEAR:
                return {"years": s}


def match_relative_english_phrase(text: str) -> tuple[int, int, str] | None:
    """If *text* matches, return ``(sign, quantity, canonical_unit_value)``.

    *sign* is ``-1`` for "... ago" and ``+1`` for "... from now" / "in ...".
    *canonical_unit_value* is the :class:`RelativeTimeUnit` string value (singular).
    """
    p = ParsedRelativePhrase.try_parse(text)
    if p is None:
        return None
    return (p.sign, p.quantity, p.unit.value)


def offset_datetime_for_relative_phrase(text: str, anchor: datetime) -> datetime | None:
    """Return *anchor* shifted by the phrase, or ``None`` if *text* is not a relative phrase."""
    p = ParsedRelativePhrase.try_parse(text)
    return None if p is None else p.offset_from(anchor)


def signed_components_for_relative_phrase(text: str) -> dict[str, int] | None:
    """Map a phrase to :class:`flex_delta` component counts (signed), or ``None``."""
    p = ParsedRelativePhrase.try_parse(text)
    return None if p is None else p.signed_flex_delta_components()
