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
PlaneName: TypeAlias = Literal["XY", "YZ", "XZ"]
FeatureOperation: TypeAlias = Literal["join", "cut"]
ExtentDirection: TypeAlias = Literal["positive", "negative"]
ParameterTarget: TypeAlias = Literal["extent"]


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


@dataclass(frozen=True)
class RectangleExtrude:
    """Extrude a centered rectangle on an XY, YZ, or XZ work plane."""

    width_mm: float
    height_mm: float
    x_mm: float
    y_mm: float
    z_mm: float
    length_mm: float
    operation: FeatureOperation = "join"
    plane: PlaneName = "XY"
    direction: ExtentDirection = "positive"

    def __post_init__(self) -> None:
        object.__setattr__(self, "width_mm", positive_mm("width_mm", self.width_mm))
        object.__setattr__(self, "height_mm", positive_mm("height_mm", self.height_mm))
        object.__setattr__(self, "x_mm", numeric_mm("x_mm", self.x_mm))
        object.__setattr__(self, "y_mm", numeric_mm("y_mm", self.y_mm))
        object.__setattr__(self, "z_mm", numeric_mm("z_mm", self.z_mm))
        object.__setattr__(self, "length_mm", positive_mm("length_mm", self.length_mm))
        if self.operation not in ("join", "cut"):
            raise InventorPlanError(f"operation={self.operation!r} must be 'join' or 'cut'.")
        if self.plane not in ("XY", "YZ", "XZ"):
            raise InventorPlanError(f"plane={self.plane!r} is unsupported.")
        if self.direction not in ("positive", "negative"):
            raise InventorPlanError(f"direction={self.direction!r} is unsupported.")

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "type": "rectangle_extrude",
            "width": _clean_number(self.width_mm),
            "height": _clean_number(self.height_mm),
            "x": _clean_number(self.x_mm),
            "y": _clean_number(self.y_mm),
            "z": _clean_number(self.z_mm),
            "length": _clean_number(self.length_mm),
            "operation": self.operation,
            "plane": self.plane,
            "direction": self.direction,
        }


@dataclass(frozen=True)
class CircleExtrude:
    """Extrude a circle on an XY, YZ, or XZ work plane."""

    diameter_mm: float
    x_mm: float
    y_mm: float
    z_mm: float
    length_mm: float
    operation: FeatureOperation = "cut"
    plane: PlaneName = "XY"
    direction: ExtentDirection = "positive"

    def __post_init__(self) -> None:
        object.__setattr__(self, "diameter_mm", positive_mm("diameter_mm", self.diameter_mm))
        object.__setattr__(self, "x_mm", numeric_mm("x_mm", self.x_mm))
        object.__setattr__(self, "y_mm", numeric_mm("y_mm", self.y_mm))
        object.__setattr__(self, "z_mm", numeric_mm("z_mm", self.z_mm))
        object.__setattr__(self, "length_mm", positive_mm("length_mm", self.length_mm))
        if self.operation not in ("join", "cut"):
            raise InventorPlanError(f"operation={self.operation!r} must be 'join' or 'cut'.")
        if self.plane not in ("XY", "YZ", "XZ"):
            raise InventorPlanError(f"plane={self.plane!r} is unsupported.")
        if self.direction not in ("positive", "negative"):
            raise InventorPlanError(f"direction={self.direction!r} is unsupported.")

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "type": "circle_extrude",
            "diameter": _clean_number(self.diameter_mm),
            "x": _clean_number(self.x_mm),
            "y": _clean_number(self.y_mm),
            "z": _clean_number(self.z_mm),
            "length": _clean_number(self.length_mm),
            "operation": self.operation,
            "plane": self.plane,
            "direction": self.direction,
        }


@dataclass(frozen=True)
class OrientedRectangleExtrude:
    """Extrude a rotated rectangle footprint on the XY plane."""

    width_mm: float
    height_mm: float
    x_mm: float
    y_mm: float
    z_mm: float
    length_mm: float
    angle_deg: float = 0.0
    operation: FeatureOperation = "join"
    direction: ExtentDirection = "positive"

    def __post_init__(self) -> None:
        object.__setattr__(self, "width_mm", positive_mm("width_mm", self.width_mm))
        object.__setattr__(self, "height_mm", positive_mm("height_mm", self.height_mm))
        object.__setattr__(self, "x_mm", numeric_mm("x_mm", self.x_mm))
        object.__setattr__(self, "y_mm", numeric_mm("y_mm", self.y_mm))
        object.__setattr__(self, "z_mm", numeric_mm("z_mm", self.z_mm))
        object.__setattr__(self, "length_mm", positive_mm("length_mm", self.length_mm))
        object.__setattr__(self, "angle_deg", numeric_mm("angle_deg", self.angle_deg))
        if self.operation not in ("join", "cut"):
            raise InventorPlanError(f"operation={self.operation!r} must be 'join' or 'cut'.")
        if self.direction not in ("positive", "negative"):
            raise InventorPlanError(f"direction={self.direction!r} is unsupported.")

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "type": "oriented_rectangle_extrude",
            "width": _clean_number(self.width_mm),
            "height": _clean_number(self.height_mm),
            "x": _clean_number(self.x_mm),
            "y": _clean_number(self.y_mm),
            "z": _clean_number(self.z_mm),
            "length": _clean_number(self.length_mm),
            "angle": _clean_number(self.angle_deg),
            "operation": self.operation,
            "direction": self.direction,
        }


@dataclass(frozen=True)
class PolygonExtrude:
    """Extrude a regular polygon footprint on the XY plane."""

    sides: int
    circumradius_mm: float
    x_mm: float
    y_mm: float
    z_mm: float
    length_mm: float
    rotation_deg: float = 0.0
    operation: FeatureOperation = "cut"
    plane: PlaneName = "XY"
    direction: ExtentDirection = "positive"

    def __post_init__(self) -> None:
        if isinstance(self.sides, bool) or self.sides < 3:
            raise InventorValidationError("sides must be at least 3.")
        object.__setattr__(self, "circumradius_mm", positive_mm("circumradius_mm", self.circumradius_mm))
        object.__setattr__(self, "x_mm", numeric_mm("x_mm", self.x_mm))
        object.__setattr__(self, "y_mm", numeric_mm("y_mm", self.y_mm))
        object.__setattr__(self, "z_mm", numeric_mm("z_mm", self.z_mm))
        object.__setattr__(self, "length_mm", positive_mm("length_mm", self.length_mm))
        object.__setattr__(self, "rotation_deg", numeric_mm("rotation_deg", self.rotation_deg))
        if self.operation not in ("join", "cut"):
            raise InventorPlanError(f"operation={self.operation!r} must be 'join' or 'cut'.")
        if self.plane not in ("XY", "YZ", "XZ"):
            raise InventorPlanError(f"plane={self.plane!r} is unsupported.")
        if self.direction not in ("positive", "negative"):
            raise InventorPlanError(f"direction={self.direction!r} is unsupported.")

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "type": "polygon_extrude",
            "sides": self.sides,
            "circumradius": _clean_number(self.circumradius_mm),
            "x": _clean_number(self.x_mm),
            "y": _clean_number(self.y_mm),
            "z": _clean_number(self.z_mm),
            "length": _clean_number(self.length_mm),
            "rotation": _clean_number(self.rotation_deg),
            "operation": self.operation,
            "plane": self.plane,
            "direction": self.direction,
        }


@dataclass(frozen=True)
class AnnularSectorExtrude:
    """Extrude an annular sector on the XY plane."""

    inner_radius_mm: float
    outer_radius_mm: float
    start_angle_deg: float
    end_angle_deg: float
    z_mm: float
    length_mm: float
    operation: FeatureOperation = "join"
    direction: ExtentDirection = "positive"

    def __post_init__(self) -> None:
        object.__setattr__(self, "inner_radius_mm", positive_mm("inner_radius_mm", self.inner_radius_mm))
        object.__setattr__(self, "outer_radius_mm", positive_mm("outer_radius_mm", self.outer_radius_mm))
        object.__setattr__(self, "start_angle_deg", numeric_mm("start_angle_deg", self.start_angle_deg))
        object.__setattr__(self, "end_angle_deg", numeric_mm("end_angle_deg", self.end_angle_deg))
        object.__setattr__(self, "z_mm", numeric_mm("z_mm", self.z_mm))
        object.__setattr__(self, "length_mm", positive_mm("length_mm", self.length_mm))
        if self.outer_radius_mm <= self.inner_radius_mm:
            raise InventorValidationError("outer radius must be greater than inner radius.")
        sweep = self.end_angle_deg - self.start_angle_deg
        if sweep <= 0 or sweep >= 360:
            raise InventorValidationError("sector angle must be between 0 and 360 degrees.")
        if self.operation not in ("join", "cut"):
            raise InventorPlanError(f"operation={self.operation!r} must be 'join' or 'cut'.")
        if self.direction not in ("positive", "negative"):
            raise InventorPlanError(f"direction={self.direction!r} is unsupported.")

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "type": "annular_sector_extrude",
            "inner_radius": _clean_number(self.inner_radius_mm),
            "outer_radius": _clean_number(self.outer_radius_mm),
            "start_angle": _clean_number(self.start_angle_deg),
            "end_angle": _clean_number(self.end_angle_deg),
            "z": _clean_number(self.z_mm),
            "length": _clean_number(self.length_mm),
            "operation": self.operation,
            "direction": self.direction,
        }


@dataclass(frozen=True)
class ProfileExtrude:
    """Extrude an arbitrary closed polygon on a principal work plane."""

    points: tuple[tuple[float, float], ...]
    plane: PlaneName
    offset_mm: float
    length_mm: float
    operation: FeatureOperation = "join"
    direction: ExtentDirection = "positive"

    def __post_init__(self) -> None:
        if len(self.points) < 3:
            raise InventorValidationError("ProfileExtrude requires at least three points.")
        object.__setattr__(
            self,
            "points",
            tuple((numeric_mm("profile_x", x), numeric_mm("profile_y", y)) for x, y in self.points),
        )
        object.__setattr__(self, "offset_mm", numeric_mm("offset_mm", self.offset_mm))
        object.__setattr__(self, "length_mm", positive_mm("length_mm", self.length_mm))
        if self.plane not in ("XY", "YZ", "XZ"):
            raise InventorPlanError(f"plane={self.plane!r} is unsupported.")
        if self.operation not in ("join", "cut"):
            raise InventorPlanError(f"operation={self.operation!r} must be 'join' or 'cut'.")
        if self.direction not in ("positive", "negative"):
            raise InventorPlanError(f"direction={self.direction!r} is unsupported.")

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "type": "profile_extrude",
            "points": [[_clean_number(x), _clean_number(y)] for x, y in self.points],
            "plane": self.plane,
            "offset": _clean_number(self.offset_mm),
            "length": _clean_number(self.length_mm),
            "operation": self.operation,
            "direction": self.direction,
        }


@dataclass(frozen=True)
class Shell:
    """Create a top-open tray by cutting the inner cavity from an outer box."""

    outer_width_mm: float
    outer_depth_mm: float
    outer_height_mm: float
    thickness_mm: float
    open_face: Literal["top"] = "top"

    def __post_init__(self) -> None:
        object.__setattr__(self, "outer_width_mm", positive_mm("outer_width_mm", self.outer_width_mm))
        object.__setattr__(self, "outer_depth_mm", positive_mm("outer_depth_mm", self.outer_depth_mm))
        object.__setattr__(self, "outer_height_mm", positive_mm("outer_height_mm", self.outer_height_mm))
        object.__setattr__(self, "thickness_mm", positive_mm("thickness_mm", self.thickness_mm))
        if self.open_face != "top":
            raise InventorPlanError(f"open_face={self.open_face!r} is unsupported.")
        if self.thickness_mm * 2 >= min(self.outer_width_mm, self.outer_depth_mm):
            raise InventorValidationError("Shell thickness leaves no positive inner footprint.")
        if self.thickness_mm >= self.outer_height_mm:
            raise InventorValidationError("Shell thickness must be smaller than outer height.")

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "type": "shell",
            "outer_width": _clean_number(self.outer_width_mm),
            "outer_depth": _clean_number(self.outer_depth_mm),
            "outer_height": _clean_number(self.outer_height_mm),
            "thickness": _clean_number(self.thickness_mm),
            "open_face": self.open_face,
        }


@dataclass(frozen=True)
class ParameterBinding:
    """Bind one generated feature property to an Inventor expression."""

    operation_index: int
    target: ParameterTarget
    expression: str

    def __post_init__(self) -> None:
        if self.operation_index < 0:
            raise InventorPlanError("ParameterBinding operation_index must be non-negative.")
        if self.target != "extent":
            raise InventorPlanError(f"Unsupported parameter target={self.target!r}.")
        if not self.expression.strip():
            raise InventorPlanError("ParameterBinding expression must not be empty.")

    def to_dict(self) -> dict[str, JsonValue]:
        return {
            "operation_index": self.operation_index,
            "target": self.target,
            "expression": self.expression,
        }


Operation: TypeAlias = (
    OuterCylinder
    | DeferredCenterBore
    | ApplyDeferredBores
    | RectangleExtrude
    | CircleExtrude
    | OrientedRectangleExtrude
    | PolygonExtrude
    | AnnularSectorExtrude
    | ProfileExtrude
    | Shell
)


@dataclass
class EnclosurePlan:
    """Two deterministic part plans for a Base/Lid enclosure."""

    name: str
    base: FeaturePlan
    lid: FeaturePlan
    parameters: dict[str, float] = field(default_factory=dict)
    units: Literal["mm"] = PUBLIC_UNIT

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        if not self.name:
            raise InventorPlanError("EnclosurePlan name must not be empty.")
        if self.units != PUBLIC_UNIT:
            raise InventorPlanError(f"EnclosurePlan units={self.units!r} must be 'mm'.")
        self.parameters = {str(key): float(value) for key, value in self.parameters.items()}
        self.validate()

    def validate(self) -> None:
        self.base.validate()
        self.lid.validate()

    def to_dict(self) -> dict[str, JsonValue]:
        self.validate()
        return {
            "name": self.name,
            "units": self.units,
            "parameters": {key: _clean_number(value) for key, value in self.parameters.items()},
            "documents": {"base": self.base.to_dict(), "lid": self.lid.to_dict()},
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def explain(self) -> str:
        self.validate()
        return "\n\n".join(
            [
                f"EnclosurePlan: {self.name}",
                f"parameters: {json.dumps(self.to_dict()['parameters'], sort_keys=True)}",
                "[Base]",
                self.base.explain(include_save=True),
                "[Lid]",
                self.lid.explain(include_save=True),
            ]
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, JsonValue]) -> "EnclosurePlan":
        name = data.get("name")
        units = data.get("units", PUBLIC_UNIT)
        parameters = data.get("parameters", {})
        documents = data.get("documents")
        if not isinstance(name, str) or not isinstance(documents, dict):
            raise InventorPlanError("EnclosurePlan requires a name and documents object.")
        if not isinstance(parameters, dict) or any(
            isinstance(value, bool) or not isinstance(value, (int, float))
            for value in parameters.values()
        ):
            raise InventorPlanError("EnclosurePlan parameters must be numeric.")
        base = documents.get("base")
        lid = documents.get("lid")
        if not isinstance(base, dict) or not isinstance(lid, dict):
            raise InventorPlanError("EnclosurePlan documents must contain base and lid objects.")
        if units != PUBLIC_UNIT:
            raise InventorPlanError(f"EnclosurePlan units={units!r} must be 'mm'.")
        return cls(
            name=name,
            units=cast(Literal["mm"], units),
            parameters={key: float(value) for key, value in parameters.items()},
            base=FeaturePlan.from_dict(cast(Mapping[str, JsonValue], base)),
            lid=FeaturePlan.from_dict(cast(Mapping[str, JsonValue], lid)),
        )

    @classmethod
    def from_json(cls, value: str) -> "EnclosurePlan":
        raw = json.loads(value)
        if not isinstance(raw, dict):
            raise InventorPlanError("EnclosurePlan JSON must decode to an object.")
        return cls.from_dict(raw)


@dataclass
class MultiPartPlan:
    """A named collection of independent part plans."""

    name: str
    parts: dict[str, FeaturePlan]
    parameters: dict[str, float] = field(default_factory=dict)
    units: Literal["mm"] = PUBLIC_UNIT

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        if not self.name:
            raise InventorPlanError("MultiPartPlan name must not be empty.")
        if not self.parts:
            raise InventorPlanError("MultiPartPlan requires at least one part.")
        if self.units != PUBLIC_UNIT:
            raise InventorPlanError(f"MultiPartPlan units={self.units!r} must be 'mm'.")
        self.parameters = {str(key): float(value) for key, value in self.parameters.items()}
        self.validate()

    def validate(self) -> None:
        for part in self.parts.values():
            part.validate()

    def to_dict(self) -> dict[str, JsonValue]:
        self.validate()
        return {
            "name": self.name,
            "units": self.units,
            "parameters": {key: _clean_number(value) for key, value in self.parameters.items()},
            "parts": {name: part.to_dict() for name, part in self.parts.items()},
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    def explain(self) -> str:
        self.validate()
        sections = [
            f"MultiPartPlan: {self.name}",
            f"parameters: {json.dumps(self.to_dict()['parameters'], sort_keys=True)}",
        ]
        for name, part in self.parts.items():
            sections.extend([f"[{name}]", part.explain(include_save=True)])
        return "\n\n".join(sections)


@dataclass
class FeaturePlan:
    """A deterministic, serializable set of geometry operations."""

    name: str
    operations: list[Operation] = field(default_factory=list)
    parameters: dict[str, float] = field(default_factory=dict)
    parameter_bindings: list[ParameterBinding] = field(default_factory=list)
    units: Literal["mm"] = PUBLIC_UNIT

    def __post_init__(self) -> None:
        self.name = self.name.strip()
        if not self.name:
            raise InventorPlanError("FeaturePlan name must not be empty.")
        if self.units != PUBLIC_UNIT:
            raise InventorPlanError(f"FeaturePlan units={self.units!r} must be 'mm'.")
        self.operations = list(self.operations)
        self.parameters = {str(key): float(value) for key, value in self.parameters.items()}
        self.parameter_bindings = list(self.parameter_bindings)
        self.validate()

    @property
    def steps(self) -> tuple[Operation, ...]:
        """Backward-compatible read-only view of planned operations."""

        return tuple(self.operations)

    def add_operation(self, operation: Operation) -> "FeaturePlan":
        return FeaturePlan(
            name=self.name,
            operations=[*self.operations, operation],
            parameters=self.parameters,
            parameter_bindings=self.parameter_bindings,
            units=self.units,
        )

    def append_plan(self, other: "FeaturePlan") -> "FeaturePlan":
        if self.units != other.units:
            raise InventorPlanError("Cannot append plans that use different units.")
        return FeaturePlan(
            name=self.name,
            operations=[*self.operations, *other.operations],
            parameters={**self.parameters, **other.parameters},
            parameter_bindings=[
                *self.parameter_bindings,
                *[
                    ParameterBinding(
                        operation_index=binding.operation_index + len(self.operations),
                        target=binding.target,
                        expression=binding.expression,
                    )
                    for binding in other.parameter_bindings
                ],
            ],
            units=self.units,
        )

    def validate(self) -> None:
        for name, value in self.parameters.items():
            if not name or isinstance(value, bool):
                raise InventorPlanError("FeaturePlan parameter names and values must be valid.")
            numeric_mm(name, value)
        for binding in self.parameter_bindings:
            if binding.operation_index >= len(self.operations):
                raise InventorPlanError(
                    f"ParameterBinding operation_index={binding.operation_index} is out of range."
                )

        outer_diameters: list[float] = []
        deferred_bores: list[DeferredCenterBore] = []
        saw_deferred = False
        applied = False
        saw_solid = False

        for index, operation in enumerate(self.operations, start=1):
            if isinstance(operation, OuterCylinder):
                if saw_deferred or applied:
                    raise InventorPlanError(
                        f"operation {index} outer_cylinder must appear before deferred bores."
                    )
                outer_diameters.append(operation.diameter_mm)
                saw_solid = True
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
            elif isinstance(
                operation,
                RectangleExtrude
                | CircleExtrude
                | OrientedRectangleExtrude
                | PolygonExtrude
                | AnnularSectorExtrude
                | ProfileExtrude,
            ):
                if operation.operation == "cut" and not saw_solid:
                    raise InventorPlanError(f"operation {index} cut requires a preceding solid.")
                if operation.operation == "join":
                    saw_solid = True
            elif isinstance(operation, Shell):
                if not saw_solid:
                    raise InventorPlanError(f"operation {index} shell requires a preceding solid.")
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
        result: dict[str, JsonValue] = {
            "name": self.name,
            "units": self.units,
            "operations": [operation.to_dict() for operation in self.operations],
        }
        if self.parameters:
            result["parameters"] = {
                key: _clean_number(value) for key, value in self.parameters.items()
            }
        if self.parameter_bindings:
            result["parameter_bindings"] = [
                binding.to_dict() for binding in self.parameter_bindings
            ]
        return result

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
            elif isinstance(operation, RectangleExtrude):
                lines.append(
                    "  "
                    f'{operation_number}. sketch_rectangle(plane="{operation.plane}", '
                    f"center=({_format_number(operation.x_mm)},{_format_number(operation.y_mm)},"
                    f"{_format_number(operation.z_mm)}), width={_format_number(operation.width_mm)}, "
                    f"height={_format_number(operation.height_mm)})"
                )
                operation_number += 1
                lines.append(
                    "  "
                    f"{operation_number}. extrude_{operation.operation}("
                    f"distance={_format_number(operation.length_mm)}, "
                    f'direction="{operation.direction}")'
                )
                operation_number += 1
            elif isinstance(operation, CircleExtrude):
                lines.append(
                    "  "
                    f'{operation_number}. sketch_circle(plane="{operation.plane}", '
                    f"center=({_format_number(operation.x_mm)},{_format_number(operation.y_mm)},"
                    f"{_format_number(operation.z_mm)}), diameter={_format_number(operation.diameter_mm)})"
                )
                operation_number += 1
                lines.append(
                    "  "
                    f"{operation_number}. extrude_{operation.operation}("
                    f"distance={_format_number(operation.length_mm)}, "
                    f'direction="{operation.direction}")'
                )
                operation_number += 1
            elif isinstance(operation, OrientedRectangleExtrude):
                lines.append(
                    "  "
                    f"{operation_number}. sketch_oriented_rectangle(center=({operation.x_mm:g},"
                    f"{operation.y_mm:g}), angle={operation.angle_deg:g}, "
                    f"width={operation.width_mm:g}, height={operation.height_mm:g})"
                )
                operation_number += 1
                lines.append(
                    "  "
                    f"{operation_number}. extrude_{operation.operation}("
                    f"distance={operation.length_mm:g}, direction=\"{operation.direction}\")"
                )
                operation_number += 1
            elif isinstance(operation, PolygonExtrude):
                lines.append(
                    "  "
                    f"{operation_number}. sketch_polygon(sides={operation.sides}, "
                    f"center=({operation.x_mm:g},{operation.y_mm:g}), "
                    f"radius={operation.circumradius_mm:g}, rotation={operation.rotation_deg:g})"
                )
                operation_number += 1
                lines.append(
                    "  "
                    f"{operation_number}. extrude_{operation.operation}("
                    f"distance={operation.length_mm:g}, direction=\"{operation.direction}\")"
                )
                operation_number += 1
            elif isinstance(operation, AnnularSectorExtrude):
                lines.append(
                    "  "
                    f"{operation_number}. sketch_annular_sector(inner={operation.inner_radius_mm:g}, "
                    f"outer={operation.outer_radius_mm:g}, angles=({operation.start_angle_deg:g},"
                    f"{operation.end_angle_deg:g}))"
                )
                operation_number += 1
            elif isinstance(operation, ProfileExtrude):
                lines.append(
                    "  "
                    f"{operation_number}. sketch_profile(plane=\"{operation.plane}\", "
                    f"points={len(operation.points)}, offset={operation.offset_mm:g})"
                )
                operation_number += 1
                lines.append(
                    "  "
                    f"{operation_number}. extrude_{operation.operation}("
                    f"distance={operation.length_mm:g}, direction=\"{operation.direction}\")"
                )
                operation_number += 1
                lines.append(
                    "  "
                    f"{operation_number}. extrude_{operation.operation}("
                    f"distance={operation.length_mm:g}, direction=\"{operation.direction}\")"
                )
                operation_number += 1
            elif isinstance(operation, Shell):
                lines.append(
                    "  "
                    f"{operation_number}. shell(open_face=\"{operation.open_face}\", "
                    f"thickness={_format_number(operation.thickness_mm)})"
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

        raw_parameters = data.get("parameters", {})
        if not isinstance(raw_parameters, dict) or any(
            not isinstance(key, str)
            or isinstance(value, bool)
            or not isinstance(value, (int, float))
            for key, value in raw_parameters.items()
        ):
            raise InventorPlanError("FeaturePlan parameters must be numeric.")
        raw_bindings = data.get("parameter_bindings", [])
        if not isinstance(raw_bindings, list):
            raise InventorPlanError("FeaturePlan parameter_bindings must be a list.")
        bindings: list[ParameterBinding] = []
        for raw_binding in raw_bindings:
            if not isinstance(raw_binding, dict):
                raise InventorPlanError("FeaturePlan parameter bindings must be objects.")
            operation_index = raw_binding.get("operation_index")
            target = raw_binding.get("target")
            expression = raw_binding.get("expression")
            if (
                isinstance(operation_index, bool)
                or not isinstance(operation_index, int)
                or target != "extent"
                or not isinstance(expression, str)
            ):
                raise InventorPlanError("Invalid FeaturePlan parameter binding.")
            bindings.append(
                ParameterBinding(
                    operation_index=operation_index,
                    target="extent",
                    expression=expression,
                )
            )

        return cls(
            name=name,
            units=cast(Literal["mm"], units),
            operations=operations,
            parameters={key: float(value) for key, value in raw_parameters.items()},
            parameter_bindings=bindings,
        )

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
    if operation_type == "rectangle_extrude":
        return RectangleExtrude(
            width_mm=float(_required_number(data, "width")),
            height_mm=float(_required_number(data, "height")),
            x_mm=float(_required_number(data, "x")),
            y_mm=float(_required_number(data, "y")),
            z_mm=float(_required_number(data, "z")),
            length_mm=float(_required_number(data, "length")),
            operation=cast(FeatureOperation, data.get("operation", "join")),
            plane=cast(PlaneName, data.get("plane", "XY")),
            direction=cast(ExtentDirection, data.get("direction", "positive")),
        )
    if operation_type == "circle_extrude":
        return CircleExtrude(
            diameter_mm=float(_required_number(data, "diameter")),
            x_mm=float(_required_number(data, "x")),
            y_mm=float(_required_number(data, "y")),
            z_mm=float(_required_number(data, "z")),
            length_mm=float(_required_number(data, "length")),
            operation=cast(FeatureOperation, data.get("operation", "cut")),
            plane=cast(PlaneName, data.get("plane", "XY")),
            direction=cast(ExtentDirection, data.get("direction", "positive")),
        )
    if operation_type == "oriented_rectangle_extrude":
        return OrientedRectangleExtrude(
            width_mm=float(_required_number(data, "width")),
            height_mm=float(_required_number(data, "height")),
            x_mm=float(_required_number(data, "x")),
            y_mm=float(_required_number(data, "y")),
            z_mm=float(_required_number(data, "z")),
            length_mm=float(_required_number(data, "length")),
            angle_deg=float(_required_number(data, "angle")),
            operation=cast(FeatureOperation, data.get("operation", "join")),
            direction=cast(ExtentDirection, data.get("direction", "positive")),
        )
    if operation_type == "polygon_extrude":
        return PolygonExtrude(
            sides=int(_required_number(data, "sides")),
            circumradius_mm=float(_required_number(data, "circumradius")),
            x_mm=float(_required_number(data, "x")),
            y_mm=float(_required_number(data, "y")),
            z_mm=float(_required_number(data, "z")),
            length_mm=float(_required_number(data, "length")),
            rotation_deg=float(_required_number(data, "rotation")),
            operation=cast(FeatureOperation, data.get("operation", "cut")),
            plane=cast(PlaneName, data.get("plane", "XY")),
            direction=cast(ExtentDirection, data.get("direction", "positive")),
        )
    if operation_type == "annular_sector_extrude":
        return AnnularSectorExtrude(
            inner_radius_mm=float(_required_number(data, "inner_radius")),
            outer_radius_mm=float(_required_number(data, "outer_radius")),
            start_angle_deg=float(_required_number(data, "start_angle")),
            end_angle_deg=float(_required_number(data, "end_angle")),
            z_mm=float(_required_number(data, "z")),
            length_mm=float(_required_number(data, "length")),
            operation=cast(FeatureOperation, data.get("operation", "join")),
            direction=cast(ExtentDirection, data.get("direction", "positive")),
        )
    if operation_type == "profile_extrude":
        raw_points = data.get("points")
        if not isinstance(raw_points, list):
            raise InventorPlanError("ProfileExtrude points must be a list.")
        points: list[tuple[float, float]] = []
        for point in raw_points:
            if not isinstance(point, list) or len(point) != 2:
                raise InventorPlanError("ProfileExtrude points must contain coordinate pairs.")
            points.append((float(_required_number({"value": point[0]}, "value")), float(_required_number({"value": point[1]}, "value"))))
        return ProfileExtrude(
            points=tuple(points),
            plane=cast(PlaneName, data.get("plane", "XY")),
            offset_mm=float(_required_number(data, "offset")),
            length_mm=float(_required_number(data, "length")),
            operation=cast(FeatureOperation, data.get("operation", "join")),
            direction=cast(ExtentDirection, data.get("direction", "positive")),
        )
    if operation_type == "shell":
        return Shell(
            outer_width_mm=float(_required_number(data, "outer_width")),
            outer_depth_mm=float(_required_number(data, "outer_depth")),
            outer_height_mm=float(_required_number(data, "outer_height")),
            thickness_mm=float(_required_number(data, "thickness")),
            open_face=cast(Literal["top"], data.get("open_face", "top")),
        )
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
