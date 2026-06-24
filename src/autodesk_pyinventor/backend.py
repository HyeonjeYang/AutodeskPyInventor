"""Autodesk Inventor COM backend."""

from __future__ import annotations

import os
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, Callable, cast

from .constants import (
    CUT_OPERATION,
    INVENTOR_PROG_ID,
    JOIN_OPERATION,
    PART_DOCUMENT_TYPE,
    POSITIVE_EXTENT_DIRECTION,
    STL_SUFFIX,
    WINDOWS_OS_NAME,
    XY_WORK_PLANE_INDEX,
)
from .documents import ensure_parent_dir, normalize_part_path, safe_template_copy
from .exceptions import (
    ExportError,
    InventorConnectionError,
    InventorNotInstalledError,
    PlanExecutionError,
    PlatformNotSupportedError,
)
from .plan import FeaturePlan, FeatureStep, JsonValue
from .units import mm_to_cm, mm_radius
from .validation import path_with_suffix

StepHandler = Callable[[Any, FeatureStep], None]


@dataclass
class InventorBackend:
    """Narrow COM executor for supported FeaturePlan steps."""

    app: Any

    @classmethod
    def connect(cls, *, visible: bool = True) -> "InventorBackend":
        if os.name != WINDOWS_OS_NAME:
            raise PlatformNotSupportedError("Autodesk Inventor COM automation is Windows-only.")

        try:
            pythoncom = cast(Any, import_module("pythoncom"))
            win32_client = cast(Any, import_module("win32com.client"))
        except ImportError as exc:
            raise InventorNotInstalledError("pywin32 is required for Inventor execution.") from exc

        pythoncom.CoInitialize()

        try:
            app = win32_client.GetActiveObject(INVENTOR_PROG_ID)
        except Exception:
            try:
                app = win32_client.Dispatch(INVENTOR_PROG_ID)
            except Exception as exc:
                raise InventorConnectionError(
                    "Could not start or connect to Autodesk Inventor through COM."
                ) from exc

        try:
            app.Visible = visible
        except Exception as exc:
            raise InventorConnectionError(
                "Connected to Inventor, but could not set visibility."
            ) from exc

        return cls(app=app)

    def new_part_document(
        self,
        *,
        name: str,
        path: Path | None = None,
        template: Path | None = None,
    ) -> Any:
        part_path = normalize_part_path(path)
        if part_path is not None:
            ensure_parent_dir(part_path)

        template_path = safe_template_copy(template) if template is not None else None
        template_arg = str(template_path) if template_path is not None else ""

        try:
            document = self.app.Documents.Add(PART_DOCUMENT_TYPE, template_arg, True)
            if name:
                _try_set_attribute(document, "DisplayName", name)
            if part_path is not None:
                document.SaveAs(str(part_path), False)
        except Exception as exc:
            raise PlanExecutionError("Could not create an Inventor part document.") from exc

        return document

    def execute_plan(self, document: Any, plan: FeaturePlan) -> None:
        handlers: dict[str, StepHandler] = {
            "base_cylinder": self._add_joined_cylinder,
            "flange_cylinder": self._add_joined_cylinder,
            "center_bore": self._cut_center_bore,
        }
        for step in plan.steps:
            handler = handlers.get(step.action)
            if handler is None:
                raise PlanExecutionError(f"Unsupported feature step: {step.action}")
            handler(document, step)

    def save_document(self, document: Any, path: Path | None = None) -> None:
        try:
            if path is None:
                document.Save()
            else:
                part_path = normalize_part_path(path)
                if part_path is None:
                    raise PlanExecutionError("A path is required to save this part.")
                ensure_parent_dir(part_path)
                document.SaveAs(str(part_path), False)
        except Exception as exc:
            raise PlanExecutionError("Could not save the Inventor document.") from exc

    def close_document(self, document: Any, *, save_changes: bool = False) -> None:
        try:
            document.Close(save_changes)
        except Exception as exc:
            raise PlanExecutionError("Could not close the Inventor document.") from exc

    def export_stl(self, document: Any, path: Path) -> None:
        stl_path = path_with_suffix("path", Path(path), (STL_SUFFIX,))
        ensure_parent_dir(stl_path)
        try:
            document.SaveAs(str(stl_path), True)
        except Exception as exc:
            raise ExportError("Could not export STL from the Inventor document.") from exc

    def _add_joined_cylinder(self, document: Any, step: FeatureStep) -> None:
        diameter_mm = _required_float(step.parameters, "diameter_mm")
        depth_mm = _required_float(step.parameters, "depth_mm")
        self._extrude_circle(
            document=document,
            diameter_mm=diameter_mm,
            depth_mm=depth_mm,
            operation=JOIN_OPERATION,
            label=_optional_string(step.parameters, "label"),
        )

    def _cut_center_bore(self, document: Any, step: FeatureStep) -> None:
        diameter_mm = _required_float(step.parameters, "diameter_mm")
        depth_mm = _required_float(step.parameters, "depth_mm")
        self._extrude_circle(
            document=document,
            diameter_mm=diameter_mm,
            depth_mm=depth_mm,
            operation=CUT_OPERATION,
            label=_optional_string(step.parameters, "label"),
        )

    def _extrude_circle(
        self,
        *,
        document: Any,
        diameter_mm: float,
        depth_mm: float,
        operation: int,
        label: str | None,
    ) -> None:
        try:
            component_definition = document.ComponentDefinition
            sketch = component_definition.Sketches.Add(
                component_definition.WorkPlanes.Item(XY_WORK_PLANE_INDEX)
            )
            transient_geometry = self.app.TransientGeometry
            center = transient_geometry.CreatePoint2d(0, 0)
            sketch.SketchCircles.AddByCenterRadius(center, mm_to_cm(mm_radius(diameter_mm)))
            profile = sketch.Profiles.AddForSolid()
            extrude_definition = (
                component_definition.Features.ExtrudeFeatures.CreateExtrudeDefinition(
                    profile, operation
                )
            )
            extrude_definition.SetDistanceExtent(
                mm_to_cm(depth_mm), POSITIVE_EXTENT_DIRECTION
            )
            feature = component_definition.Features.ExtrudeFeatures.Add(extrude_definition)
            if label:
                _try_set_attribute(feature, "Name", label)
        except Exception as exc:
            raise PlanExecutionError(
                f"Could not execute feature step '{label or 'circle'}'."
            ) from exc


def _required_float(parameters: dict[str, JsonValue], key: str) -> float:
    value = parameters.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PlanExecutionError(f"Feature step parameter '{key}' must be numeric.")
    return float(value)


def _optional_string(parameters: dict[str, JsonValue], key: str) -> str | None:
    value = parameters.get(key)
    return value if isinstance(value, str) else None


def _try_set_attribute(target: Any, name: str, value: object) -> bool:
    try:
        setattr(target, name, value)
    except Exception:
        return False
    return True
