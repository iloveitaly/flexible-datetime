"""English relative time phrases (e.g. "12 weeks ago").

dateutil fuzzy parsing mis-reads these as literal calendar dates; flex_delta's compact
parser rejects the trailing "ago". Shared matching keeps flex_datetime and flex_delta
aligned.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta

from dateutil.relativedelta import relativedelta

_REL_WORD_UNITS = (
    r"microseconds?|milliseconds?|seconds?|minutes?|hours?|days?|weeks?|months?|years?"
)
_REL_AGO_RE = re.compile(
    rf"^\s*(?P<n>a|an|\d+)\s+(?P<unit>{_REL_WORD_UNITS})\s+ago\s*$",
    re.IGNORECASE,
)
_REL_FROM_NOW_RE = re.compile(
    rf"^\s*(?P<n>a|an|\d+)\s+(?P<unit>{_REL_WORD_UNITS})\s+from\s+now\s*$",
    re.IGNORECASE,
)
_REL_IN_RE = re.compile(
    rf"^\s*in\s+(?P<n>a|an|\d+)\s+(?P<unit>{_REL_WORD_UNITS})\s*$",
    re.IGNORECASE,
)


def _quantity_from_match(n_group: str) -> int:
    lowered = n_group.lower()
    if lowered in ("a", "an"):
        return 1
    return int(n_group)


def match_relative_english_phrase(text: str) -> tuple[int, int, str] | None:
    """If *text* is a supported phrase, return ``(sign, quantity, unit_lower)``.

    *sign* is ``-1`` for \"… ago\" and ``+1`` for \"… from now\" / \"in …\".
    """
    t = text.strip()
    if not t:
        return None
    if m := _REL_AGO_RE.fullmatch(t):
        return (-1, _quantity_from_match(m.group("n")), m.group("unit").lower())
    if m := _REL_FROM_NOW_RE.fullmatch(t):
        return (1, _quantity_from_match(m.group("n")), m.group("unit").lower())
    if m := _REL_IN_RE.fullmatch(t):
        return (1, _quantity_from_match(m.group("n")), m.group("unit").lower())
    return None


def offset_datetime_for_relative_phrase(text: str, anchor: datetime) -> datetime | None:
    """Return *anchor* shifted by the phrase, or ``None`` if *text* is not a relative phrase."""
    matched = match_relative_english_phrase(text)
    if not matched:
        return None
    sign, n, unit = matched
    if unit.startswith("microsecond"):
        return anchor + timedelta(microseconds=sign * n)
    if unit.startswith("millisecond"):
        return anchor + timedelta(milliseconds=sign * n)
    if unit.startswith("second"):
        return anchor + timedelta(seconds=sign * n)
    if unit.startswith("minute"):
        return anchor + timedelta(minutes=sign * n)
    if unit.startswith("hour"):
        return anchor + timedelta(hours=sign * n)
    if unit.startswith("day"):
        return anchor + timedelta(days=sign * n)
    if unit.startswith("week"):
        return anchor + timedelta(weeks=sign * n)
    if unit.startswith("month"):
        return anchor + relativedelta(months=sign * n)
    if unit.startswith("year"):
        return anchor + relativedelta(years=sign * n)
    raise ValueError(f"Unsupported relative unit: {unit!r}")


def signed_components_for_relative_phrase(text: str) -> dict[str, int] | None:
    """Map a phrase to :class:`flex_delta` component counts (signed), or ``None``."""
    matched = match_relative_english_phrase(text)
    if not matched:
        return None
    sign, n, unit = matched
    if unit.startswith("microsecond"):
        return {"microseconds": sign * n}
    if unit.startswith("millisecond"):
        return {"microseconds": sign * n * 1000}
    if unit.startswith("second"):
        return {"seconds": sign * n}
    if unit.startswith("minute"):
        return {"minutes": sign * n}
    if unit.startswith("hour"):
        return {"hours": sign * n}
    if unit.startswith("day"):
        return {"days": sign * n}
    if unit.startswith("week"):
        return {"weeks": sign * n}
    if unit.startswith("month"):
        return {"months": sign * n}
    if unit.startswith("year"):
        return {"years": sign * n}
    raise ValueError(f"Unsupported relative unit: {unit!r}")
