from dataclasses import fields
from typing import TypeVar, Type

from mashumaro.mixins.json import DataClassJSONMixin

T = TypeVar("T", bound="DataClassJSONSerializer")


class ValidationError(Exception):
    pass


class DataClassJSONSerializer(DataClassJSONMixin):

    @classmethod
    def __post_deserialize__(cls: Type[T], obj: T) -> T:
        errors = {}

        for field in fields(obj):
            func = getattr(obj, f"_post_deserialize_{field.name}", None)

            if callable(func):
                try:
                    func(obj)
                except AssertionError as e:
                    errors[field.name] = str(e)
        if errors:
            raise ValidationError(errors)
        return obj
