"""Serializable Base/Lid assembly planning and Inventor execution."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .app import InventorApp
from .constants import ASSEMBLY_SUFFIX, PART_SUFFIX, PUBLIC_UNIT
from .documents import ensure_parent_dir
from .exceptions import InventorDocumentError, InventorPlanError
from .units import mm_to_cm
from .validation import path_with_suffix, positive_mm


@dataclass(frozen=True)
class EnclosureAssemblyPlan:
    """Place a Base at the origin and a Lid at Base top height."""

    base_input: Path | None = None
    lid_input: Path | None = None
    output: Path | None = None
    base_h_mm: float = 29.5
    name: str = "astro_controller"
    units: str = PUBLIC_UNIT

    def __post_init__(self) -> None:
        object.__setattr__(self, "base_h_mm", positive_mm("base_h", self.base_h_mm))
        if not self.name.strip():
            raise InventorPlanError("Assembly plan name must not be empty.")
        if self.units != PUBLIC_UNIT:
            raise InventorPlanError("Assembly plan units must be 'mm'.")
        for field_name, path, suffixes in (
            ("base_input", self.base_input, (PART_SUFFIX,)),
            ("lid_input", self.lid_input, (PART_SUFFIX,)),
            ("output", self.output, (ASSEMBLY_SUFFIX,)),
        ):
            if path is not None:
                path_with_suffix(field_name, Path(path), suffixes)

    @property
    def base_translation_mm(self) -> tuple[float, float, float]:
        return (0.0, 0.0, 0.0)

    @property
    def lid_translation_mm(self) -> tuple[float, float, float]:
        return (0.0, 0.0, self.base_h_mm)

    def validate_for_execution(self) -> None:
        if self.base_input is None or self.lid_input is None or self.output is None:
            raise InventorPlanError(
                "--base-input, --lid-input, and --output are required for assembly execution."
            )
        for label, path in (("base_input", self.base_input), ("lid_input", self.lid_input)):
            if not path.is_file():
                raise InventorDocumentError(f"{label} does not exist: {path}")
        if self.output.exists():
            raise InventorDocumentError(f"Refusing to overwrite existing assembly: {self.output}")

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "units": self.units,
            "base_input": None if self.base_input is None else str(self.base_input),
            "lid_input": None if self.lid_input is None else str(self.lid_input),
            "output": None if self.output is None else str(self.output),
            "occurrences": [
                {"name": "Base", "translation": list(self.base_translation_mm)},
                {"name": "Lid", "translation": list(self.lid_translation_mm)},
            ],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "EnclosureAssemblyPlan":
        occurrences = data.get("occurrences")
        if not isinstance(occurrences, list) or len(occurrences) != 2:
            raise InventorPlanError("Assembly plan requires Base and Lid occurrences.")
        lid = occurrences[1]
        if not isinstance(lid, dict):
            raise InventorPlanError("Assembly Lid occurrence must be an object.")
        translation = lid.get("translation")
        if (
            not isinstance(translation, list)
            or len(translation) != 3
            or any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in translation)
            or float(translation[0]) != 0
            or float(translation[1]) != 0
        ):
            raise InventorPlanError("Assembly Lid translation must lie on the Z axis.")
        return cls(
            name=str(data.get("name", "astro_controller")),
            units=str(data.get("units", PUBLIC_UNIT)),
            base_input=_optional_path(data.get("base_input")),
            lid_input=_optional_path(data.get("lid_input")),
            output=_optional_path(data.get("output")),
            base_h_mm=float(translation[2]),
        )

    @classmethod
    def from_json(cls, value: str) -> "EnclosureAssemblyPlan":
        raw = json.loads(value)
        if not isinstance(raw, dict):
            raise InventorPlanError("Assembly plan JSON must decode to an object.")
        return cls.from_dict(raw)


@dataclass
class Assembly:
    """A narrow facade around one Inventor assembly document."""

    app: InventorApp
    document: Any
    path: Path
    closed: bool = False

    @classmethod
    def from_plan(cls, *, app: InventorApp, plan: EnclosureAssemblyPlan) -> "Assembly":
        plan.validate_for_execution()
        assert plan.base_input is not None
        assert plan.lid_input is not None
        assert plan.output is not None
        ensure_parent_dir(plan.output)
        document: Any | None = None
        try:
            document = app.backend.new_assembly_document()
            component_definition = document.ComponentDefinition
            transient_geometry = app.raw.TransientGeometry
            for part_path, translation in (
                (plan.base_input, plan.base_translation_mm),
                (plan.lid_input, plan.lid_translation_mm),
            ):
                matrix = transient_geometry.CreateMatrix()
                vector = transient_geometry.CreateVector(
                    *[mm_to_cm(value) for value in translation]
                )
                matrix.SetTranslation(vector)
                component_definition.Occurrences.Add(str(part_path.resolve()), matrix)
            document.SaveAs(str(plan.output.resolve()), False)
            return cls(app=app, document=document, path=plan.output)
        except Exception:
            if document is not None:
                try:
                    document.Close(False)
                except Exception:
                    pass
            raise

    def close(self) -> None:
        if not self.closed:
            self.app.backend.close_document(self.document, save_changes=False)
            self.closed = True


def _optional_path(value: object) -> Path | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise InventorPlanError("Assembly paths must be strings or null.")
    return Path(value)
