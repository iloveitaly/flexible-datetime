import json
from datetime import date, datetime
from enum import StrEnum
from typing import Any, ClassVar

import arrow
from pydantic import (
    BaseModel,
    Field,
    PrivateAttr,
    field_serializer,
    field_validator,
    model_validator,
)

import flexible_datetime.pydantic_arrow  # noqa: F401
from flexible_datetime._base import FlexDateTimeMixin, binary_to_mask, default_mask, mask_to_binary


class OutputFormat(StrEnum):
    """
    Enum for the output formats of FlexDateTime.

    minimal_datetime: Serialize as shortest possible datetime format.
        Examples:
            YYYY, YYYY-MM, YYYY-MM-DD, YYYY-MM-DD HH, YYYY-MM-DD HH:mm, YYYY-MM-DD HH:mm:ss

    datetime: Serialize as full datetime format.
        Example: YYYY-MM-DD HH:mm:ss

    flex: Serialize as a dict format with the datetime and mask.
        Example: {"dt": "2023-06-29T12:30:45+00:00", "mask": "0011111"}

    components: Serialize as a dict format with masked components.
        Example: {"year": 2023, "month": 6, "day": 29, "hour": 12, "minute": 30, "second": 45, "millisecond": 0}
    """

    minimal_datetime = "minimal_datetime"
    datetime = "datetime"
    flex = "flex"
    components = "components"


class FlexDateTime(FlexDateTimeMixin, BaseModel):
    dt: arrow.Arrow = Field(default_factory=arrow.utcnow)
    mask: dict = Field(default_factory=default_mask)

    _SHORT_DATETIME_FMT: ClassVar[str] = "YYYY-MM-DD HH:mm:ss"
    _BOUNDARY_RE: ClassVar[str] = r"^\D+|\D+$"
    _default_output_format: ClassVar[OutputFormat] = OutputFormat.minimal_datetime
    _output_format: OutputFormat = PrivateAttr(default=_default_output_format)

    def __init__(self, *args, **kwargs):
        if args and args[0] is None:
            raise ValueError("Cannot parse None as a FlexDateTime.")
        if not args and not kwargs:
            super().__init__(dt=arrow.utcnow())
        elif args and isinstance(args[0], dict):
            d = args[0]
            is_dict_format = any(k in d for k in default_mask())
            if "dt" not in kwargs and is_dict_format:
                dt, mask = self._components_from_dict(d)
                super().__init__(dt=dt, mask=mask)
            else:
                super().__init__(*args, **kwargs)
        elif args and isinstance(args[0], str):
            dt, mask = self._components_from_str(args[0])
            super().__init__(dt=dt, mask=mask)
        elif args and isinstance(args[0], FlexDateTimeMixin):
            super().__init__(dt=args[0].dt, mask=args[0].mask)
        elif args and isinstance(args[0], datetime):
            super().__init__(dt=arrow.get(args[0]))
        elif args and isinstance(args[0], arrow.Arrow):
            super().__init__(dt=args[0])
        elif args and isinstance(args[0], date):
            super().__init__(
                dt=arrow.get(args[0]),
                mask=binary_to_mask("0001111"),
            )
        else:
            super().__init__(*args, **kwargs)

    @model_validator(mode="before")
    def custom_validate_before(cls, values):
        if not values:
            return values
        elif isinstance(values, datetime):
            return {"dt": arrow.get(values)}
        elif isinstance(values, arrow.Arrow):
            return {"dt": values}
        elif isinstance(values, str):
            return {"dt": arrow.get(values)}
        elif isinstance(values, FlexDateTimeMixin):
            return {"dt": values.dt, "mask": values.mask}
        return values

    def model_dump(self, *args, **kwargs) -> dict[str, Any]:
        if self._default_output_format == OutputFormat.datetime:
            return {"dt": str(self.dt)}
        return super().model_dump(*args, **kwargs)

    def model_dump_json(self, *args, **kwargs):
        if self._default_output_format == OutputFormat.datetime:
            return json.dumps({"dt": str(self.dt)})
        return super().model_dump_json(*args, **kwargs)

    @field_serializer("mask")
    def serialize_mask(self, mask: dict) -> str:
        return mask_to_binary(mask)

    @field_validator("mask", mode="before")
    def deserialize_mask(cls, value):
        if isinstance(value, str):
            return binary_to_mask(value)
        return value

    def to_str(self, output_fmt: str | None = None) -> str:
        return self.to_short_datetime(output_fmt)

    def __str__(self) -> str:
        if self._output_format == OutputFormat.datetime:
            return str(self.dt)
        elif self._output_format == OutputFormat.minimal_datetime:
            return self.to_short_datetime()
        elif self._output_format == OutputFormat.components:
            return str(self.to_components())
        return str(self.to_flex())

    def __repr__(self) -> str:
        return self.model_dump_json()
