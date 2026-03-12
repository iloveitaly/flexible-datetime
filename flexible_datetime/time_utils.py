import re

from dateutil.parser import parse
from dateutil.parser._parser import ParserError


def infer_time_format(date_str: str) -> str:
    """
    Infers the date format from the given date string, including handling various formats.
    """
    # Remove any leading/trailing whitespace
    # Remove any leading/trailing whitespace
    date_str = date_str.strip()

    # Check for common formats
    formats = [
        (r"^\d{4}$", "YYYY"),
        (r"^\d{6}$", "YYYYMM"),
        (r"^\d{8}$", "YYYYMMDD"),
        (r"^\d{4}[-/]\d{2}$", "YYYY-MM"),
        (r"^\d{4}[-/]\d{2}[-/]\d{2}$", "YYYY-MM-DD"),
        (r"^\d{4}[-/]\d{2}[-/]\d{2}[T ]\d{2}$", "YYYY-MM-DD[T]HH"),
        (r"^\d{4}[-/]\d{2}[-/]\d{2}[T ]\d{2}:\d{2}$", "YYYY-MM-DD[T]HH:mm"),
        (r"^\d{4}[-/]\d{2}[-/]\d{2}[T ]\d{2}:\d{2}:\d{2}$", "YYYY-MM-DD[T]HH:mm:ss"),
        (r"^\d{8}T\d{4}$", "YYYYMMDDTHHmm"),
        (r"^\d{8}T\d{6}$", "YYYYMMDDTHHmmss"),
        (r"^\d{8}T\d{6}\.\d{3}$", "YYYYMMDDTHHmmssSSS"),
        (r"^\d{8}T\d{6}\.\d{6}$", "YYYYMMDDTHHmmssSSSSSS"),
        (
            r"^\d{4}[-/]\d{2}[-/]\d{2}[T ]\d{2}:\d{2}:\d{2}\.\d{3}$",
            "YYYY-MM-DD[T]HH:mm:ssSSS",
        ),
        (
            r"^\d{4}[-/]\d{2}[-/]\d{2}[T ]\d{2}:\d{2}:\d{2}\.\d{6}$",
            "YYYY-MM-DD[T]HH:mm:ssSSSSSS",
        ),
        (r"^\d{8}T\d{6}\.\d{6}Z$", "YYYYMMDDTHHmmssSSSSSSZZ"),
        (
            r"^\d{4}[-/]\d{2}[-/]\d{2}[T ]\d{2}:\d{2}:\d{2}\.\d{6}Z$",
            "%Y-%m-%dT%H:%M:%S.%f%z",
        ),
    ]

    for pattern, fmt in formats:
        if re.match(pattern, date_str):
            # Replace [T] with T or space based on the input
            return fmt.replace("[T]", "T" if "T" in date_str else " ")

    # If no match found, try to parse and infer
    try:
        dt = parse(date_str)
        separator = "T" if "T" in date_str else " "
        fmt = f"YYYY-MM-DD{separator}HH:mm:ss"
        if dt.microsecond:
            fmt += "SSSSSS"
        if dt.tzinfo:
            fmt += "ZZ"
        return fmt
    except ValueError:
        raise ParserError(f"Unknown date format for {date_str}")
