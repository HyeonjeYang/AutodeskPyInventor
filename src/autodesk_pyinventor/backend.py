"""Autodesk Inventor COM backend."""

from __future__ import annotations

import os
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

from .constants import (
    ASSEMBLY_DOCUMENT_TYPE,
    CUT_OPERATION,
    INVENTOR_PROG_ID,
    JOIN_OPERATION,
    PART_DOCUMENT_TYPE,
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
from .plan import (
    ApplyDeferredBores,
    AnnularSectorExtrude,
    CircleExtrude,
    DeferredCenterBore,
    FeaturePlan,
    OuterCylinder,
    OrientedRectangleExtrude,
    PolygonExtrude,
    RectangleExtrude,
    Shell,
)
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
            INV = win32_client.constants
        except Exception as ensure_exc:
            try:
                app = win32_client.dynamic.Dispatch(INVENTOR_PROG_ID)
                INV = _inventor_fallback_constants()
            except Exception as dynamic_exc:
                raise InventorConnectionError(
                    "Inventor COM connection failed. Make sure Autodesk Inventor is installed. "
                    f"EnsureDispatch error: {ensure_exc}; dynamic Dispatch error: {dynamic_exc}"
                ) from dynamic_exc

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
        part_document_type = self._constant("kPartDocumentObject")
        if int(getattr(document, "DocumentType", 0)) != part_document_type:
            raise InventorDocumentError(
                f"Opened document at {copied_path}, but it is not an Inventor part document."
            )

        if name:
            _try_set_attribute(document, "DisplayName", name)
        return document

    def execute_plan(self, document: Any, plan: FeaturePlan) -> None:
        plan.validate()
        self._add_user_parameters(document, plan.parameters)
        deferred_bore: DeferredCenterBore | None = None
        bindings = {binding.operation_index: binding for binding in plan.parameter_bindings}
        for operation_index, operation in enumerate(plan.operations):
            feature: Any | None = None
            if isinstance(operation, OuterCylinder):
                feature = self._add_outer_cylinder(document, operation)
            elif isinstance(operation, DeferredCenterBore):
                if deferred_bore is not None:
                    raise InventorPlanError("Only one deferred center bore is supported.")
                deferred_bore = operation
            elif isinstance(operation, ApplyDeferredBores):
                if deferred_bore is None:
                    raise InventorPlanError("apply_deferred_bores requires a deferred bore.")
                feature = self._apply_center_bore_once(document, deferred_bore)
                deferred_bore = None
            elif isinstance(operation, RectangleExtrude):
                feature = self._add_rectangle_extrude(document, operation)
            elif isinstance(operation, CircleExtrude):
                feature = self._add_circle_extrude(document, operation)
            elif isinstance(operation, OrientedRectangleExtrude):
                feature = self._add_oriented_rectangle_extrude(document, operation)
            elif isinstance(operation, PolygonExtrude):
                feature = self._add_polygon_extrude(document, operation)
            elif isinstance(operation, AnnularSectorExtrude):
                feature = self._add_annular_sector_extrude(document, operation)
            elif isinstance(operation, Shell):
                feature = self._add_shell(document, operation)
            binding = bindings.get(operation_index)
            if binding is not None:
                self._bind_feature_parameter(feature, binding.expression)

    def _add_user_parameters(self, document: Any, parameters: dict[str, float]) -> None:
        if not parameters:
            return
        try:
            user_parameters = document.ComponentDefinition.Parameters.UserParameters
            for name, value in parameters.items():
                expression = f"{value:g} mm"
                try:
                    user_parameters.Item(name).Expression = expression
                except Exception:
                    user_parameters.AddByExpression(name, expression, "mm")
        except Exception as exc:
            raise InventorGeometryError(
                f"Could not create Inventor UserParameters. Original COM error: {exc}"
            ) from exc

    def _bind_feature_parameter(self, feature: Any | None, expression: str) -> None:
        if feature is None:
            raise InventorGeometryError(
                f"Could not bind feature extent to parameter expression {expression!r}."
            )
        for getter in (
            lambda: feature.Extent.Distance,
            lambda: feature.Definition.Extent.Distance,
            lambda: feature.Definition.Distance,
        ):
            try:
                getter().Expression = expression
                return
            except Exception:
                continue
        raise InventorGeometryError(
            f"Inventor did not expose a distance parameter for expression {expression!r}."
        )

    def save_document(self, document: Any) -> None:
        try:
            document.Save()
        except Exception as exc:
            raise InventorDocumentError(
                f"Could not save the Inventor document. Original COM error: {exc}"
            ) from exc

    def new_assembly_document(self) -> Any:
        try:
            return self.app.Documents.Add(self._constant("kAssemblyDocumentObject"))
        except Exception as exc:
            raise InventorDocumentError(
                f"Could not create an Inventor assembly document. Original COM error: {exc}"
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

    def _add_outer_cylinder(self, document: Any, operation: OuterCylinder) -> Any:
        return self._extrude_circle(
            document=document,
            diameter_mm=operation.diameter_mm,
            x_mm=0,
            y_mm=0,
            z_mm=operation.z_mm,
            plane="XY",
            operation=self._constant("kJoinOperation"),
            label="outer cylinder",
            distance_mm=operation.length_mm,
            direction="positive",
            through_all_symmetric=False,
        )

    def _apply_center_bore_once(self, document: Any, operation: DeferredCenterBore) -> Any:
        return self._extrude_circle(
            document=document,
            diameter_mm=operation.diameter_mm,
            x_mm=0,
            y_mm=0,
            z_mm=0,
            plane="XY",
            operation=self._constant("kCutOperation"),
            label="center bore",
            distance_mm=None,
            direction="positive",
            through_all_symmetric=True,
        )

    def _add_circle_extrude(self, document: Any, operation: CircleExtrude) -> Any:
        return self._extrude_circle(
            document=document,
            diameter_mm=operation.diameter_mm,
            x_mm=operation.x_mm,
            y_mm=operation.y_mm,
            z_mm=operation.z_mm,
            plane=operation.plane,
            operation=self._constant(
                "kJoinOperation" if operation.operation == "join" else "kCutOperation"
            ),
            label=f"circle {operation.operation}",
            distance_mm=operation.length_mm,
            direction=operation.direction,
            through_all_symmetric=False,
        )

    def _add_rectangle_extrude(self, document: Any, operation: RectangleExtrude) -> Any:
        return self._extrude_rectangle(
            document=document,
            width_mm=operation.width_mm,
            height_mm=operation.height_mm,
            x_mm=operation.x_mm,
            y_mm=operation.y_mm,
            z_mm=operation.z_mm,
            plane=operation.plane,
            operation=self._constant(
                "kJoinOperation" if operation.operation == "join" else "kCutOperation"
            ),
            label=f"rectangle {operation.operation}",
            distance_mm=operation.length_mm,
            direction=operation.direction,
        )

    def _add_shell(self, document: Any, operation: Shell) -> Any:
        # A controlled inner-box cut is more reliable across Inventor versions than
        # ShellFeatures, while producing the same open-top tray geometry.
        return self._extrude_rectangle(
            document=document,
            width_mm=operation.outer_width_mm - 2 * operation.thickness_mm,
            height_mm=operation.outer_depth_mm - 2 * operation.thickness_mm,
            x_mm=operation.outer_width_mm / 2,
            y_mm=operation.outer_depth_mm / 2,
            z_mm=operation.thickness_mm,
            plane="XY",
            operation=self._constant("kCutOperation"),
            label="shell inner cavity",
            distance_mm=operation.outer_height_mm - operation.thickness_mm,
            direction="positive",
        )

    def _extrude_circle(
        self,
        *,
        document: Any,
        diameter_mm: float,
        x_mm: float,
        y_mm: float,
        z_mm: float,
        plane: str,
        operation: int,
        label: str,
        distance_mm: float | None,
        direction: str,
        through_all_symmetric: bool,
    ) -> Any:
        try:
            component_definition = document.ComponentDefinition
            center_u_mm, center_v_mm, offset_mm = _plane_coordinates(
                plane,
                x_mm=x_mm,
                y_mm=y_mm,
                z_mm=z_mm,
            )
            work_plane = self._work_plane_for_plane(component_definition, plane, offset_mm)
            sketch = component_definition.Sketches.Add(work_plane)
            transient_geometry = self.app.TransientGeometry
            center = transient_geometry.CreatePoint2d(
                mm_to_cm(center_u_mm),
                mm_to_cm(center_v_mm),
            )
            sketch.SketchCircles.AddByCenterRadius(center, mm_to_cm(mm_radius(diameter_mm)))
            profile = sketch.Profiles.AddForSolid()
            extrude_definition = (
                component_definition.Features.ExtrudeFeatures.CreateExtrudeDefinition(
                    profile,
                    operation,
                )
            )
            if through_all_symmetric:
                extrude_definition.SetThroughAllExtent(self._constant("kSymmetricExtentDirection"))
            elif distance_mm is not None:
                extrude_definition.SetDistanceExtent(
                    mm_to_cm(distance_mm),
                    self._extent_direction(direction),
                )
            else:
                raise InventorPlanError(
                    "distance_mm is required unless through_all_symmetric is set."
                )

            feature = component_definition.Features.ExtrudeFeatures.Add(extrude_definition)
            _try_set_attribute(feature, "Name", label)
            return feature
        except InventorGeometryError:
            raise
        except Exception as exc:
            raise InventorGeometryError(
                f"Could not create {label} with diameter {diameter_mm:g} mm. "
                f"Original COM error: {exc}"
            ) from exc

    def _extrude_rectangle(
        self,
        *,
        document: Any,
        width_mm: float,
        height_mm: float,
        x_mm: float,
        y_mm: float,
        z_mm: float,
        plane: str,
        operation: int,
        label: str,
        distance_mm: float,
        direction: str,
    ) -> Any:
        try:
            component_definition = document.ComponentDefinition
            center_u_mm, center_v_mm, offset_mm = _plane_coordinates(
                plane,
                x_mm=x_mm,
                y_mm=y_mm,
                z_mm=z_mm,
            )
            work_plane = self._work_plane_for_plane(component_definition, plane, offset_mm)
            sketch = component_definition.Sketches.Add(work_plane)
            transient_geometry = self.app.TransientGeometry
            corner_a = transient_geometry.CreatePoint2d(
                mm_to_cm(center_u_mm - width_mm / 2),
                mm_to_cm(center_v_mm - height_mm / 2),
            )
            corner_b = transient_geometry.CreatePoint2d(
                mm_to_cm(center_u_mm + width_mm / 2),
                mm_to_cm(center_v_mm + height_mm / 2),
            )
            sketch.SketchLines.AddAsTwoPointRectangle(corner_a, corner_b)
            profile = sketch.Profiles.AddForSolid()
            extrude_definition = (
                component_definition.Features.ExtrudeFeatures.CreateExtrudeDefinition(
                    profile,
                    operation,
                )
            )
            extrude_definition.SetDistanceExtent(
                mm_to_cm(distance_mm),
                self._extent_direction(direction),
            )
            feature = component_definition.Features.ExtrudeFeatures.Add(extrude_definition)
            _try_set_attribute(feature, "Name", label)
            return feature
        except InventorGeometryError:
            raise
        except Exception as exc:
            raise InventorGeometryError(
                f"Could not create {label} with rectangle {width_mm:g} x {height_mm:g} mm. "
                f"Original COM error: {exc}"
            ) from exc

    def _add_oriented_rectangle_extrude(
        self,
        document: Any,
        operation: OrientedRectangleExtrude,
    ) -> Any:
        try:
            component_definition = document.ComponentDefinition
            work_plane = self._work_plane_for_plane(component_definition, "XY", operation.z_mm)
            sketch = component_definition.Sketches.Add(work_plane)
            points = _rotated_rectangle_points(
                self.app.TransientGeometry,
                operation.x_mm,
                operation.y_mm,
                operation.width_mm,
                operation.height_mm,
                operation.angle_deg,
            )
            for index, start in enumerate(points):
                sketch.SketchLines.AddByTwoPoints(start, points[(index + 1) % len(points)])
            profile = sketch.Profiles.AddForSolid()
            definition = component_definition.Features.ExtrudeFeatures.CreateExtrudeDefinition(
                profile,
                self._constant(
                    "kJoinOperation" if operation.operation == "join" else "kCutOperation"
                ),
            )
            definition.SetDistanceExtent(
                mm_to_cm(operation.length_mm),
                self._extent_direction(operation.direction),
            )
            feature = component_definition.Features.ExtrudeFeatures.Add(definition)
            _try_set_attribute(feature, "Name", f"oriented rectangle {operation.operation}")
            return feature
        except Exception as exc:
            raise InventorGeometryError(
                f"Could not create oriented rectangle at ({operation.x_mm:g}, {operation.y_mm:g}). "
                f"Original COM error: {exc}"
            ) from exc

    def _add_polygon_extrude(self, document: Any, operation: PolygonExtrude) -> Any:
        try:
            component_definition = document.ComponentDefinition
            work_plane = self._work_plane_for_plane(component_definition, "XY", operation.z_mm)
            sketch = component_definition.Sketches.Add(work_plane)
            points = _polygon_points(
                self.app.TransientGeometry,
                operation.sides,
                operation.circumradius_mm,
                operation.x_mm,
                operation.y_mm,
                operation.rotation_deg,
            )
            for index, start in enumerate(points):
                sketch.SketchLines.AddByTwoPoints(start, points[(index + 1) % len(points)])
            profile = sketch.Profiles.AddForSolid()
            definition = component_definition.Features.ExtrudeFeatures.CreateExtrudeDefinition(
                profile,
                self._constant(
                    "kJoinOperation" if operation.operation == "join" else "kCutOperation"
                ),
            )
            definition.SetDistanceExtent(
                mm_to_cm(operation.length_mm),
                self._extent_direction(operation.direction),
            )
            feature = component_definition.Features.ExtrudeFeatures.Add(definition)
            _try_set_attribute(feature, "Name", f"polygon {operation.operation}")
            return feature
        except Exception as exc:
            raise InventorGeometryError(
                f"Could not create polygon with {operation.sides} sides. Original COM error: {exc}"
            ) from exc

    def _add_annular_sector_extrude(
        self,
        document: Any,
        operation: AnnularSectorExtrude,
    ) -> Any:
        try:
            component_definition = document.ComponentDefinition
            work_plane = self._work_plane_for_plane(component_definition, "XY", operation.z_mm)
            sketch = component_definition.Sketches.Add(work_plane)
            transient_geometry = self.app.TransientGeometry
            center = transient_geometry.CreatePoint2d(0, 0)
            outer_start = _polar_point(
                transient_geometry, operation.outer_radius_mm, operation.start_angle_deg
            )
            outer_end = _polar_point(
                transient_geometry, operation.outer_radius_mm, operation.end_angle_deg
            )
            inner_start = _polar_point(
                transient_geometry, operation.inner_radius_mm, operation.start_angle_deg
            )
            inner_end = _polar_point(
                transient_geometry, operation.inner_radius_mm, operation.end_angle_deg
            )
            sketch.SketchArcs.AddByCenterStartEnd(center, outer_start, outer_end)
            sketch.SketchLines.AddByTwoPoints(outer_end, inner_end)
            sketch.SketchArcs.AddByCenterStartEnd(center, inner_end, inner_start)
            sketch.SketchLines.AddByTwoPoints(inner_start, outer_start)
            profile = sketch.Profiles.AddForSolid()
            definition = component_definition.Features.ExtrudeFeatures.CreateExtrudeDefinition(
                profile,
                self._constant(
                    "kJoinOperation" if operation.operation == "join" else "kCutOperation"
                ),
            )
            definition.SetDistanceExtent(
                mm_to_cm(operation.length_mm),
                self._extent_direction(operation.direction),
            )
            feature = component_definition.Features.ExtrudeFeatures.Add(definition)
            _try_set_attribute(feature, "Name", f"annular sector {operation.operation}")
            return feature
        except Exception as exc:
            raise InventorGeometryError(
                "Could not create annular sector. Original COM error: " f"{exc}"
            ) from exc

    def _extent_direction(self, direction: str) -> int:
        if direction == "positive":
            return self._constant("kPositiveExtentDirection")
        if direction == "negative":
            return self._constant("kNegativeExtentDirection")
        raise InventorPlanError(f"Unsupported extent direction={direction!r}.")

    def _work_plane_for_z(self, component_definition: Any, z_mm: float) -> Any:
        return self._work_plane_for_plane(component_definition, "XY", z_mm)

    def _work_plane_for_plane(self, component_definition: Any, plane: str, offset_mm: float) -> Any:
        plane_indexes = {"YZ": 1, "XZ": 2, "XY": XY_WORK_PLANE_INDEX}
        if plane not in plane_indexes:
            raise InventorPlanError(f"Unsupported work plane={plane!r}.")
        work_planes = component_definition.WorkPlanes
        base_plane = work_planes.Item(plane_indexes[plane])
        if abs(offset_mm) < 1e-9:
            return base_plane
        try:
            offset_plane = work_planes.AddByPlaneAndOffset(base_plane, mm_to_cm(offset_mm))
            _try_set_attribute(offset_plane, "Visible", False)
            return offset_plane
        except Exception as exc:
            raise InventorGeometryError(
                f"Could not create offset work plane at {plane} offset={offset_mm:g} mm. "
                f"Original COM error: {exc}"
            ) from exc

    def _constant(self, name: str) -> int:
        value = getattr(self.constants, name, None)
        if value is None:
            raise InventorGeometryError(
                f"Inventor constant {name} is unavailable. "
                "Try clearing the win32com gen_py cache."
            )
        return int(value)


def _try_set_attribute(target: Any, name: str, value: object) -> bool:
    try:
        setattr(target, name, value)
    except Exception:
        return False
    return True


def _inventor_fallback_constants() -> Any:
    """Return the small documented enum subset used by this backend."""

    return SimpleNamespace(
        kPartDocumentObject=PART_DOCUMENT_TYPE,
        kAssemblyDocumentObject=ASSEMBLY_DOCUMENT_TYPE,
        kJoinOperation=JOIN_OPERATION,
        kCutOperation=CUT_OPERATION,
        kPositiveExtentDirection=POSITIVE_EXTENT_DIRECTION,
        kNegativeExtentDirection=20994,
        kSymmetricExtentDirection=20995,
    )


def _cast_to_part_document(document: Any) -> Any:
    try:
        win32_client = cast(Any, import_module("win32com.client"))
        return win32_client.CastTo(document, "PartDocument")
    except Exception:
        return document


def _plane_coordinates(
    plane: str,
    *,
    x_mm: float,
    y_mm: float,
    z_mm: float,
) -> tuple[float, float, float]:
    if plane == "XY":
        return x_mm, y_mm, z_mm
    if plane == "YZ":
        return y_mm, z_mm, x_mm
    if plane == "XZ":
        return x_mm, z_mm, y_mm
    raise InventorPlanError(f"Unsupported work plane={plane!r}.")


def _polar_point(transient_geometry: Any, radius_mm: float, angle_deg: float) -> Any:
    import math

    angle = math.radians(angle_deg)
    return transient_geometry.CreatePoint2d(
        mm_to_cm(radius_mm * math.cos(angle)),
        mm_to_cm(radius_mm * math.sin(angle)),
    )


def _rotated_rectangle_points(
    transient_geometry: Any,
    center_x_mm: float,
    center_y_mm: float,
    width_mm: float,
    height_mm: float,
    angle_deg: float,
) -> list[Any]:
    import math

    angle = math.radians(angle_deg)
    cos_angle = math.cos(angle)
    sin_angle = math.sin(angle)
    points: list[Any] = []
    for local_x, local_y in (
        (-width_mm / 2, -height_mm / 2),
        (width_mm / 2, -height_mm / 2),
        (width_mm / 2, height_mm / 2),
        (-width_mm / 2, height_mm / 2),
    ):
        x_mm = center_x_mm + local_x * cos_angle - local_y * sin_angle
        y_mm = center_y_mm + local_x * sin_angle + local_y * cos_angle
        points.append(transient_geometry.CreatePoint2d(mm_to_cm(x_mm), mm_to_cm(y_mm)))
    return points


def _polygon_points(
    transient_geometry: Any,
    sides: int,
    radius_mm: float,
    center_x_mm: float,
    center_y_mm: float,
    rotation_deg: float,
) -> list[Any]:
    import math

    return [
        transient_geometry.CreatePoint2d(
            mm_to_cm(center_x_mm + radius_mm * math.cos(math.radians(rotation_deg + index * 360 / sides))),
            mm_to_cm(center_y_mm + radius_mm * math.sin(math.radians(rotation_deg + index * 360 / sides))),
        )
        for index in range(sides)
    ]
