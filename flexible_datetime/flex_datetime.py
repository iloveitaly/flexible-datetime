from __future__ import annotations

import json
from datetime import date, datetime, timedelta
from enum import StrEnum
from typing import Any, ClassVar, TypeAlias, overload

import arrow
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema

import flexible_datetime.pydantic_arrow  # noqa: F401
from flexible_datetime._base import FlexDateTimeMixin, binary_to_mask, default_mask

FlextimeInput: TypeAlias = (
    "str | FlexDateTimeMixin | date | datetime | arrow.Arrow | dict | flex_datetime | None"
)


class OutputFormat(StrEnum):
    """
    Enum for the output formats of flex_datetime.

    short_datetime: Serialize as shortest possible datetime format.
        Examples:
            YYYY, YYYY-MM, YYYY-MM-DD, YYYY-MM-DD HH, YYYY-MM-DD HH:mm, YYYY-MM-DD HH:mm:ss

    datetime: Serialize as full datetime format.
        Example: YYYY-MM-DD HH:mm:ss

    mask: Serialize as JSON-compatible format.
        Example: {"dt": "2023-06-29T12:30:45+00:00", "mask": "0011111"}

    component: Serialize as JSON-compatible format with masked components.
        Example: {"year": 2023, "month": 6, "day": 29, "hour": 12, "minute": 30, "second": 45, "millisecond": 0}
    """

    short = "short"
    datetime = "datetime"
    mask = "mask"
    components = "components"


class flex_datetime(FlexDateTimeMixin):
    _default_output_format: ClassVar[OutputFormat] = OutputFormat.short

    def __init__(self, *args: FlextimeInput, **kwargs: Any):
        self.dt = arrow.utcnow()
        self.mask = default_mask()
        self._output_format: OutputFormat | None = None

        if args and args[0] is None:
            raise ValueError("Cannot parse None as a flex_datetime.")
        if not args and not kwargs:
            return
        if args:
            if isinstance(args[0], dict):
                d = args[0]
                is_dict_format = any(k in d for k in default_mask())
                if "dt" not in kwargs and is_dict_format:
                    dt, mask = self._components_from_dict(d)
                    self.dt = dt
                    self.mask = mask
                else:
                    self.dt = arrow.get(d["dt"])
                    if "mask" in d and isinstance(d["mask"], dict):
                        self.mask = d["mask"]
                    elif "mask" in d and isinstance(d["mask"], str):
                        self.mask = binary_to_mask(d["mask"])
            elif isinstance(args[0], str):
                dt, mask = self._components_from_str(args[0])
                self.dt = dt
                self.mask = mask
            elif isinstance(args[0], FlexDateTimeMixin):
                self.dt = args[0].dt
                self.mask = args[0].mask
            elif isinstance(args[0], datetime) or isinstance(args[0], arrow.Arrow):
                self.dt = arrow.get(args[0])
            elif isinstance(args[0], date):
                self.dt = arrow.get(args[0])
                self.mask.update({
                    "hour": True,
                    "minute": True,
                    "second": True,
                    "millisecond": True,
                })
            else:
                raise ValueError(f"Unsupported input: {args}")
            return

        if "dt" in kwargs:
            self.dt = arrow.get(kwargs["dt"])
            if "mask" in kwargs:
                if isinstance(kwargs["mask"], dict):
                    self.mask = kwargs["mask"]
                elif isinstance(kwargs["mask"], str):
                    self.mask = binary_to_mask(kwargs["mask"])
                else:
                    raise ValueError(f"Invalid mask: {kwargs['mask']}")
        else:
            raise NotImplementedError(f"Unsupported input: {args} {kwargs}")

    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        def flex_datetime_serialization(value: flex_datetime, _, info) -> str:
            return str(value)

        return core_schema.no_info_after_validator_function(
            function=cls.validate,
            schema=core_schema.union_schema([
                core_schema.str_schema(),
                core_schema.dict_schema(),
                core_schema.is_instance_schema(flex_datetime),
                core_schema.is_instance_schema(datetime),
                core_schema.is_instance_schema(arrow.Arrow),
                core_schema.is_instance_schema(cls),
                core_schema.no_info_plain_validator_function(cls),
            ]),
            serialization=core_schema.wrap_serializer_function_ser_schema(
                flex_datetime_serialization, info_arg=True
            ),
        )

    @classmethod
    def validate(cls, value) -> flex_datetime:
        if isinstance(value, flex_datetime):
            return value
        return flex_datetime(value)

    def to_str(self, output_format: str | None = None) -> str:
        output_format = output_format or self._output_format
        if output_format is None:
            output_format = self._default_output_format
        if output_format == OutputFormat.datetime:
            return str(self.dt)
        elif output_format == OutputFormat.short:
            return self.to_short_datetime()
        elif output_format == OutputFormat.components:
            return str(self.to_components())
        return str(self.to_flex())

    def to_json(self, output_format: str | None = None) -> str:
        return self.to_str(output_format)

    def __json__(self) -> str:
        return self.to_json()

    @classmethod
    def from_json(cls, json_str: str) -> flex_datetime:
        return flex_datetime(json.loads(json_str))

    def __str__(self) -> str:
        return self.to_str()

    def __repr__(self) -> str:
        return str(self)

    # --- Output format property ---

    @property
    def output_format(self) -> OutputFormat | None:
        return self._output_format

    @output_format.setter
    def output_format(self, format: OutputFormat | str | None) -> None:
        if isinstance(format, str):
            try:
                format = OutputFormat(format)
            except ValueError:
                valid_formats = [f.value for f in OutputFormat]
                raise ValueError(f"Invalid format '{format}'. Must be one of: {valid_formats}")
        if not isinstance(format, OutputFormat):
            raise ValueError("Format must be an OutputFormat enum value or a valid format string")
        self._output_format = format

    @classmethod
    def set_default_output_format(cls, format: OutputFormat | str) -> None:
        if isinstance(format, str):
            try:
                format = OutputFormat(format)
            except ValueError:
                valid_formats = [f.value for f in OutputFormat]
                raise ValueError(f"Invalid format '{format}'. Must be one of: {valid_formats}")
        if not isinstance(format, OutputFormat):
            raise ValueError("Format must be an OutputFormat enum value or a valid format string")
        cls._default_output_format = format

    # --- Arithmetic ---

    @overload
    def __sub__(self, other: flex_datetime | datetime) -> timedelta: ...

    @overload
    def __sub__(self, other: timedelta) -> flex_datetime: ...

    def __sub__(self, other: flex_datetime | datetime | timedelta) -> timedelta | flex_datetime:
        if isinstance(other, flex_datetime | datetime | arrow.Arrow):
            other_dt = arrow.get(other.dt if isinstance(other, flex_datetime) else other)
            return self.dt - other_dt
        elif isinstance(other, timedelta):
            new_dt = self.dt - other
            result = flex_datetime(new_dt)
            result.mask = self.mask.copy()
            return result
        return NotImplemented

    def __add__(self, other: timedelta) -> flex_datetime:
        if isinstance(other, timedelta):
            new_dt = self.dt + other
            result = flex_datetime(new_dt)
            result.mask = self.mask.copy()
            return result
        return NotImplemented

    def __radd__(self, other: timedelta) -> flex_datetime:
        return self.__add__(other)

    def __rsub__(self, other: datetime | flex_datetime) -> timedelta:
        if isinstance(other, datetime | flex_datetime):
            other_dt = arrow.get(other.dt if isinstance(other, flex_datetime) else other)
            return other_dt - self.dt
        return NotImplemented

    @classmethod
    def __get_validators__(cls):
        yield cls.validate


short_datetime = type(
    "short_datetime", (flex_datetime,), {"_default_output_format": OutputFormat.short}
)

dict_datetime = type(
    "dict_datetime", (flex_datetime,), {"_default_output_format": OutputFormat.components}
)

iso_datetime = type(
    "iso_datetime", (flex_datetime,), {"_default_output_format": OutputFormat.datetime}
)

mask_datetime = type(
    "flexible_time", (flex_datetime,), {"_default_output_format": OutputFormat.mask}
)


try:
    import beanie.odm.utils.encoder as encoder  # type: ignore

    def flex_datetime_encoder(value: flex_datetime) -> str:
        return value.to_json()

    encoder.DEFAULT_CUSTOM_ENCODERS[flex_datetime] = flex_datetime_encoder
except ImportError:
    pass
