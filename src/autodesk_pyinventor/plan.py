"""Serializable feature planning primitives."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Mapping, Sequence, TypeAlias, cast

from .constants import PUBLIC_UNIT
from .exceptions import ValidationError

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


def _assert_jsonable(value: JsonValue) -> None:
    try:
        json.dumps(value)
    except TypeError as exc:
        raise ValidationError("Feature plans must contain JSON-serializable values.") from exc


def _json_mapping(value: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    result = dict(value)
    _assert_jsonable(result)
    return result


@dataclass(frozen=True)
class FeatureStep:
    """A single serializable operation for the Inventor backend."""

    action: str
    parameters: dict[str, JsonValue] = field(default_factory=dict)
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        action = self.action.strip()
        if not action:
            raise ValidationError("Feature step action must not be empty.")
        object.__setattr__(self, "action", action)
        object.__setattr__(self, "parameters", _json_mapping(self.parameters))
        object.__setattr__(self, "notes", tuple(str(note) for note in self.notes))

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "action": self.action,
            "parameters": dict(self.parameters),
            "notes": list(self.notes),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, JsonValue]) -> "FeatureStep":
        action = data.get("action")
        if not isinstance(action, str):
            raise ValidationError("Feature step action must be a string.")

        raw_parameters = data.get("parameters", {})
        if not isinstance(raw_parameters, dict):
            raise ValidationError("Feature step parameters must be an object.")
        parameters = cast(dict[str, JsonValue], raw_parameters)

        raw_notes = data.get("notes", [])
        if not isinstance(raw_notes, list) or not all(isinstance(note, str) for note in raw_notes):
            raise ValidationError("Feature step notes must be a list of strings.")

        return cls(action=action, parameters=parameters, notes=tuple(raw_notes))


@dataclass(frozen=True)
class FeaturePlan:
    """A deterministic, serializable set of feature operations."""

    name: str
    units: str = PUBLIC_UNIT
    steps: tuple[FeatureStep, ...] = ()
    metadata: dict[str, JsonValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        name = self.name.strip()
        if not name:
            raise ValidationError("Feature plan name must not be empty.")
        if self.units != PUBLIC_UNIT:
            raise ValidationError(f"Only {PUBLIC_UNIT}-first feature plans are supported.")
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "steps", tuple(self.steps))
        object.__setattr__(self, "metadata", _json_mapping(self.metadata))

    def add_step(
        self,
        action: str,
        parameters: Mapping[str, JsonValue] | None = None,
        notes: Sequence[str] = (),
    ) -> "FeaturePlan":
        step = FeatureStep(action=action, parameters=dict(parameters or {}), notes=tuple(notes))
        return FeaturePlan(
            name=self.name,
            units=self.units,
            steps=(*self.steps, step),
            metadata=dict(self.metadata),
        )

    def append_plan(self, other: "FeaturePlan") -> "FeaturePlan":
        if self.units != other.units:
            raise ValidationError("Cannot append plans that use different units.")

        metadata = dict(self.metadata)
        history = metadata.get("recipe_history", [])
        if not isinstance(history, list):
            history = []
        recipe = other.metadata.get("recipe")
        if isinstance(recipe, str):
            history = [*history, recipe]
        metadata["recipe_history"] = history

        return FeaturePlan(
            name=self.name,
            units=self.units,
            steps=(*self.steps, *other.steps),
            metadata=metadata,
        )

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "name": self.name,
            "units": self.units,
            "metadata": dict(self.metadata),
            "steps": [step.to_dict() for step in self.steps],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True)

    @classmethod
    def from_dict(cls, data: Mapping[str, JsonValue]) -> "FeaturePlan":
        name = data.get("name")
        units = data.get("units", PUBLIC_UNIT)
        if not isinstance(name, str):
            raise ValidationError("Feature plan name must be a string.")
        if not isinstance(units, str):
            raise ValidationError("Feature plan units must be a string.")

        raw_metadata = data.get("metadata", {})
        if not isinstance(raw_metadata, dict):
            raise ValidationError("Feature plan metadata must be an object.")
        metadata = cast(dict[str, JsonValue], raw_metadata)

        raw_steps = data.get("steps", [])
        if not isinstance(raw_steps, list):
            raise ValidationError("Feature plan steps must be a list.")

        step_data: list[Mapping[str, JsonValue]] = []
        for step in raw_steps:
            if not isinstance(step, dict):
                raise ValidationError("Feature plan steps must be objects.")
            step_data.append(cast(Mapping[str, JsonValue], step))
        steps = tuple(FeatureStep.from_dict(step) for step in step_data)

        return cls(name=name, units=units, steps=steps, metadata=metadata)

    @classmethod
    def from_json(cls, value: str) -> "FeaturePlan":
        raw = json.loads(value)
        if not isinstance(raw, dict):
            raise ValidationError("Feature plan JSON must decode to an object.")
        return cls.from_dict(raw)

    def summary(self) -> list[str]:
        return [f"{index + 1}. {step.action}" for index, step in enumerate(self.steps)]
