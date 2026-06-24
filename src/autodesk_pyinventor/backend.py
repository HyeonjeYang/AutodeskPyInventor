"""Autodesk Inventor COM backend."""

from __future__ import annotations

import os
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from typing import Any, cast

from .constants import (
    CUT_OPERATION,
    INVENTOR_PROG_ID,
    JOIN_OPERATION,
    POSITIVE_EXTENT_DIRECTION,
    STL_SUFFIX,
    WINDOWS_OS_NAME,
    XY_WORK_PLANE_INDEX,
)
from .documents import copy_template_to_part, find_standard_part_template, require_part_path
from .exceptions import (
    InventorConnectionError,
    InventorDocumentError,
    InventorExportError,
    InventorGeometryError,
    InventorNotInstalledError,
    InventorPlanError,
    PlatformNotSupportedError,
)
from .plan import ApplyDeferredBores, DeferredCenterBore, FeaturePlan, OuterCylinder
from .units import mm_to_cm, mm_radius
from .validation import path_with_suffix


@dataclass
class InventorBackend:
    """Narrow COM executor for supported FeaturePlan operations."""

    app: Any
    constants: Any

    @classmethod
    def connect(cls, *, visible: bool = True) -> "InventorBackend":
        if os.name != WINDOWS_OS_NAME:
            raise PlatformNotSupportedError("Autodesk Inventor COM automation is Windows-only.")

        try:
            pythoncom = cast(Any, import_module("pythoncom"))
            win32_client = cast(Any, import_module("win32com.client"))
        except ImportError as exc:
            raise InventorNotInstalledError(
                "pywin32 is not installed. Run: python -m pip install pywin32"
            ) from exc

        pythoncom.CoInitialize()

        try:
            app = win32_client.gencache.EnsureDispatch(INVENTOR_PROG_ID)
        except Exception as exc:
            raise InventorConnectionError(
                "Inventor COM connection failed. Make sure Autodesk Inventor is installed. "
                f"Original COM error: {exc}"
            ) from exc

        INV = win32_client.constants

        try:
            app.Visible = visible
        except Exception as exc:
            raise InventorConnectionError(
                "Connected to Inventor, but could not set visibility. "
                f"Original COM error: {exc}"
            ) from exc

        return cls(app=app, constants=INV)

    def new_part_document(
        self,
        *,
        name: str,
        path: str | Path | None,
        template: str | Path | None = None,
    ) -> Any:
        part_path = require_part_path(path)
        template_path = find_standard_part_template(
            self.app,
            template=template,
            constants=self.constants,
        )
        copied_path = copy_template_to_part(template_path, part_path)

        try:
            document = self.app.Documents.Open(str(copied_path), True)
        except Exception as exc:
            raise InventorDocumentError(
                f"Could not open copied part template at {copied_path}. "
                "Check that the directory exists and is writable. "
                f"Original COM error: {exc}"
            ) from exc

        document = _cast_to_part_document(document)
        part_document_type = self._constant("kPartDocumentObject", 12290)
        if int(getattr(document, "DocumentType", 0)) != part_document_type:
            raise InventorDocumentError(
                f"Opened document at {copied_path}, but it is not an Inventor part document."
            )

        if name:
            _try_set_attribute(document, "DisplayName", name)
        return document

    def execute_plan(self, document: Any, plan: FeaturePlan) -> None:
        plan.validate()
        deferred_bore: DeferredCenterBore | None = None
        for operation in plan.operations:
            if isinstance(operation, OuterCylinder):
                self._add_outer_cylinder(document, operation)
            elif isinstance(operation, DeferredCenterBore):
                if deferred_bore is not None:
                    raise InventorPlanError("Only one deferred center bore is supported.")
                deferred_bore = operation
            elif isinstance(operation, ApplyDeferredBores):
                if deferred_bore is None:
                    raise InventorPlanError("apply_deferred_bores requires a deferred bore.")
                self._apply_center_bore_once(document, deferred_bore)
                deferred_bore = None

    def save_document(self, document: Any) -> None:
        try:
            document.Save()
        except Exception as exc:
            raise InventorDocumentError(
                f"Could not save the Inventor document. Original COM error: {exc}"
            ) from exc

    def close_document(self, document: Any, *, save_changes: bool = False) -> None:
        try:
            document.Close(save_changes)
        except Exception as exc:
            raise InventorDocumentError(
                f"Could not close the Inventor document. Original COM error: {exc}"
            ) from exc

    def export_stl(self, document: Any, path: str | Path) -> None:
        stl_path = path_with_suffix("path", Path(path), (STL_SUFFIX,))
        stl_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            document.SaveAs(str(stl_path), True)
        except Exception as exc:
            raise InventorExportError(
                f"Could not export STL to {stl_path}. Original COM error: {exc}"
            ) from exc

    def _add_outer_cylinder(self, document: Any, operation: OuterCylinder) -> None:
        self._extrude_circle(
            document=document,
            diameter_mm=operation.diameter_mm,
            z_mm=operation.z_mm,
            operation=self._constant("kJoinOperation", JOIN_OPERATION),
            label="outer cylinder",
            distance_mm=operation.length_mm,
            through_all_symmetric=False,
        )

    def _apply_center_bore_once(self, document: Any, operation: DeferredCenterBore) -> None:
        self._extrude_circle(
            document=document,
            diameter_mm=operation.diameter_mm,
            z_mm=0,
            operation=self._constant("kCutOperation", CUT_OPERATION),
            label="center bore",
            distance_mm=None,
            through_all_symmetric=True,
        )

    def _extrude_circle(
        self,
        *,
        document: Any,
        diameter_mm: float,
        z_mm: float,
        operation: int,
        label: str,
        distance_mm: float | None,
        through_all_symmetric: bool,
    ) -> None:
        try:
            component_definition = document.ComponentDefinition
            work_plane = self._work_plane_for_z(component_definition, z_mm)
            sketch = component_definition.Sketches.Add(work_plane)
            transient_geometry = self.app.TransientGeometry
            center = transient_geometry.CreatePoint2d(0, 0)
            sketch.SketchCircles.AddByCenterRadius(center, mm_to_cm(mm_radius(diameter_mm)))
            profile = sketch.Profiles.AddForSolid()
            extrude_definition = (
                component_definition.Features.ExtrudeFeatures.CreateExtrudeDefinition(
                    profile,
                    operation,
                )
            )
            if through_all_symmetric:
                extrude_definition.SetThroughAllExtent(
                    self._constant("kSymmetricExtentDirection", POSITIVE_EXTENT_DIRECTION)
                )
            elif distance_mm is not None:
                extrude_definition.SetDistanceExtent(
                    mm_to_cm(distance_mm),
                    self._constant("kPositiveExtentDirection", POSITIVE_EXTENT_DIRECTION),
                )
            else:
                raise InventorPlanError(
                    "distance_mm is required unless through_all_symmetric is set."
                )

            feature = component_definition.Features.ExtrudeFeatures.Add(extrude_definition)
            _try_set_attribute(feature, "Name", label)
        except Exception as exc:
            raise InventorGeometryError(
                f"Could not create {label} with diameter {diameter_mm:g} mm. "
                f"Original COM error: {exc}"
            ) from exc

    def _work_plane_for_z(self, component_definition: Any, z_mm: float) -> Any:
        work_planes = component_definition.WorkPlanes
        xy_plane = work_planes.Item(XY_WORK_PLANE_INDEX)
        if abs(z_mm) < 1e-9:
            return xy_plane

        try:
            offset_plane = work_planes.AddByPlaneAndOffset(xy_plane, mm_to_cm(z_mm))
            _try_set_attribute(offset_plane, "Visible", False)
            return offset_plane
        except Exception as exc:
            raise InventorGeometryError(
                f"Could not create offset work plane at z={z_mm:g} mm. "
                f"Original COM error: {exc}"
            ) from exc

    def _constant(self, name: str, fallback: int) -> int:
        return int(getattr(self.constants, name, fallback))


def _try_set_attribute(target: Any, name: str, value: object) -> bool:
    try:
        setattr(target, name, value)
    except Exception:
        return False
    return True


def _cast_to_part_document(document: Any) -> Any:
    try:
        win32_client = cast(Any, import_module("win32com.client"))
        return win32_client.CastTo(document, "PartDocument")
    except Exception:
        return document
