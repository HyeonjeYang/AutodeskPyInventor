"""Serializable feature planning primitives."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Mapping, TypeAlias, cast

from .constants import PUBLIC_UNIT
from .exceptions import InventorPlanError, InventorValidationError
from .validation import non_negative_mm, numeric_mm, positive_mm

JsonScalar: TypeAlias = str | int | float | bool | None
JsonValue: TypeAlias = JsonScalar | list["JsonValue"] | dict[str, "JsonValue"]


def _clean_number(value: float) -> int | float:
    return int(value) if value.is_integer() else value


def _format_number(value: float) -> str:
    clean = _clean_number(value)
    return str(clean)


def _path_text(path: str | Path | None) -> str:
    if path is None:
        return "<not provided>"
    return str(path).replace("\\", "/")


@dataclass(frozen=True)
class OuterCylinder:
    """A solid cylinder to join into the part body."""

    diameter_mm: float
    z_mm: float
    length_mm: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "diameter_mm", positive_mm("diameter_mm", self.diameter_mm))
        object.__setattr__(self, "z_mm", numeric_mm("z_mm", self.z_mm))
        object.__setattr__(self, "length_mm", positive_mm("length_mm", self.length_mm))

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "type": "outer_cylinder",
            "diameter": _clean_number(self.diameter_mm),
            "z": _clean_number(self.z_mm),
            "length": _clean_number(self.length_mm),
        }


@dataclass(frozen=True)
class DeferredCenterBore:
    """A center bore to apply once after all outer cylinders are joined."""

    diameter_mm: float
    axis: Literal["Z"] = "Z"

    def __post_init__(self) -> None:
        object.__setattr__(self, "diameter_mm", positive_mm("diameter_mm", self.diameter_mm))
        if self.axis != "Z":
            raise InventorValidationError(f"axis={self.axis!r} must be 'Z'.")

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "type": "deferred_center_bore",
            "diameter": _clean_number(self.diameter_mm),
            "axis": self.axis,
        }


@dataclass(frozen=True)
class ApplyDeferredBores:
    """Apply the deferred center bore once using a through-all symmetric cut."""

    def to_dict(self) -> dict[str, JsonValue]:
        return {"type": "apply_deferred_bores"}


Operation: TypeAlias = OuterCylinder | DeferredCenterBore | ApplyDeferredBores


@dataclass
class FeaturePlan:
    """A deterministic, serializable set of geometry operations."""

    name: str
    operations: list[Operation] = field(default_factory=list)
    units: Literal["mm"] = PUBLIC_UNIT

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        if not self.name:
            raise InventorPlanError("FeaturePlan name must not be empty.")
        if self.units != PUBLIC_UNIT:
            raise InventorPlanError(f"FeaturePlan units={self.units!r} must be 'mm'.")
        self.operations = list(self.operations)
        self.validate()

    @property
    def steps(self) -> tuple[Operation, ...]:
        """Backward-compatible read-only view of planned operations."""

        return tuple(self.operations)

    def add_operation(self, operation: Operation) -> "FeaturePlan":
        return FeaturePlan(
            name=self.name,
            operations=[*self.operations, operation],
            units=self.units,
        )

    def append_plan(self, other: "FeaturePlan") -> "FeaturePlan":
        if self.units != other.units:
            raise InventorPlanError("Cannot append plans that use different units.")
        return FeaturePlan(
            name=self.name,
            operations=[*self.operations, *other.operations],
            units=self.units,
        )

    def validate(self) -> None:
        outer_diameters: list[float] = []
        deferred_bores: list[DeferredCenterBore] = []
        saw_deferred = False
        applied = False

        for index, operation in enumerate(self.operations, start=1):
            if isinstance(operation, OuterCylinder):
                if saw_deferred or applied:
                    raise InventorPlanError(
                        f"operation {index} outer_cylinder must appear before deferred bores."
                    )
                outer_diameters.append(operation.diameter_mm)
            elif isinstance(operation, DeferredCenterBore):
                if applied:
                    raise InventorPlanError(
                        f"operation {index} deferred_center_bore must appear before apply."
                    )
                saw_deferred = True
                deferred_bores.append(operation)
            elif isinstance(operation, ApplyDeferredBores):
                if applied:
                    raise InventorPlanError("apply_deferred_bores may appear only once.")
                if not deferred_bores:
                    raise InventorPlanError(
                        "apply_deferred_bores requires a deferred_center_bore first."
                )
                applied = True
            else:
                raise InventorPlanError(
                    f"operation {index} has unsupported type {type(operation)!r}."
                )

        if deferred_bores and not applied:
            raise InventorPlanError("deferred_center_bore requires apply_deferred_bores.")
        if len(deferred_bores) > 1:
            raise InventorPlanError("Only one deferred_center_bore is supported in v0.1.")
        if outer_diameters and deferred_bores:
            bore = deferred_bores[0]
            smallest_outer = min(outer_diameters)
            if bore.diameter_mm >= smallest_outer:
                raise InventorValidationError(
                    "diameter_mm="
                    f"{bore.diameter_mm:g} must be smaller than outer diameter "
                    f"{smallest_outer:g}."
                )

    def to_dict(self) -> dict[str, JsonValue]:
        self.validate()
        return {
            "name": self.name,
            "units": self.units,
            "operations": [operation.to_dict() for operation in self.operations],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def explain(
        self,
        *,
        path: str | Path | None = None,
        template: str | Path | None = "standard.ipt",
        include_save: bool = True,
    ) -> str:
        self.validate()
        lines = [f"FeaturePlan: {self.name}", f"units: {self.units}", "operations:"]
        operation_number = 1
        lines.append(
            "  "
            f'{operation_number}. create_part_document(path="{_path_text(path)}", '
            f'template="{_path_text(template)}")'
        )
        operation_number += 1
        last_bore: DeferredCenterBore | None = None

        for operation in self.operations:
            if isinstance(operation, OuterCylinder):
                lines.append(
                    "  "
                    f'{operation_number}. sketch_circle(plane="XY", '
                    f"z={_format_number(operation.z_mm)}, "
                    f"diameter={_format_number(operation.diameter_mm)})"
                )
                operation_number += 1
                lines.append(
                    "  "
                    f"{operation_number}. extrude_join("
                    f"distance={_format_number(operation.length_mm)})"
                )
                operation_number += 1
            elif isinstance(operation, DeferredCenterBore):
                last_bore = operation
                lines.append(
                    "  "
                    f"{operation_number}. defer_bore("
                    f"diameter={_format_number(operation.diameter_mm)}, "
                    f'axis="{operation.axis}")'
                )
                operation_number += 1
            elif isinstance(operation, ApplyDeferredBores):
                if last_bore is None:
                    raise InventorPlanError("apply_deferred_bores requires a deferred bore.")
                lines.append(
                    "  "
                    f"{operation_number}. apply_center_bore_once("
                    f"diameter={_format_number(last_bore.diameter_mm)}, "
                    'extent="through_all_symmetric")'
                )
                operation_number += 1

        if include_save:
            lines.append(f"  {operation_number}. save()")

        return "\n".join(lines)

    def summary(self) -> list[str]:
        return [
            f"{index}. {operation.to_dict()['type']}"
            for index, operation in enumerate(self.operations, start=1)
        ]

    @classmethod
    def from_dict(cls, data: Mapping[str, JsonValue]) -> "FeaturePlan":
        name = data.get("name")
        units = data.get("units", PUBLIC_UNIT)
        if not isinstance(name, str):
            raise InventorPlanError("FeaturePlan name must be a string.")
        if units != PUBLIC_UNIT:
            raise InventorPlanError(f"FeaturePlan units={units!r} must be 'mm'.")

        raw_operations = data.get("operations", [])
        if not isinstance(raw_operations, list):
            raise InventorPlanError("FeaturePlan operations must be a list.")

        operations = [
            operation_from_dict(cast(Mapping[str, JsonValue], operation))
            for operation in raw_operations
            if isinstance(operation, dict)
        ]
        if len(operations) != len(raw_operations):
            raise InventorPlanError("FeaturePlan operations must be objects.")

        return cls(name=name, units=cast(Literal["mm"], units), operations=operations)

    @classmethod
    def from_json(cls, value: str) -> "FeaturePlan":
        raw = json.loads(value)
        if not isinstance(raw, dict):
            raise InventorPlanError("FeaturePlan JSON must decode to an object.")
        return cls.from_dict(raw)


def operation_from_dict(data: Mapping[str, JsonValue]) -> Operation:
    operation_type = data.get("type")
    if operation_type == "outer_cylinder":
        return OuterCylinder(
            diameter_mm=float(_required_number(data, "diameter")),
            z_mm=float(_required_number(data, "z")),
            length_mm=float(_required_number(data, "length")),
        )
    if operation_type == "deferred_center_bore":
        axis = data.get("axis", "Z")
        if axis != "Z":
            raise InventorPlanError(f"axis={axis!r} must be 'Z'.")
        return DeferredCenterBore(
            diameter_mm=float(_required_number(data, "diameter")),
            axis="Z",
        )
    if operation_type == "apply_deferred_bores":
        return ApplyDeferredBores()
    raise InventorPlanError(f"Unsupported operation type={operation_type!r}.")


def _required_number(data: Mapping[str, JsonValue], key: str) -> int | float:
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InventorPlanError(f"{key}={value!r} must be numeric.")
    return value


def validate_bore_argument(name: str, value: float, outer_name: str, outer: float) -> None:
    bore = non_negative_mm(name, value)
    if bore >= outer:
        raise InventorValidationError(
            f"{name}={bore:g} must be smaller than {outer_name}={outer:g}."
        )
