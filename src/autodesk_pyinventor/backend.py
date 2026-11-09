"""Autodesk Inventor COM backend."""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Literal, cast

from .constants import (
    ASSEMBLY_DOCUMENT_TYPE,
    CIRCLE_CURVE_TYPE,
    CUT_OPERATION,
    FILE_BROWSE_IO_MECHANISM,
    INVENTOR_PROG_ID,
    JOIN_OPERATION,
    NEGATIVE_EXTENT_DIRECTION,
    PART_DOCUMENT_TYPE,
    POSITIVE_EXTENT_DIRECTION,
    STL_EXPORT_UNITS_MM,
    STL_RESOLUTION_VALUES,
    STL_SUFFIX,
    STL_TRANSLATOR_ADDIN_ID,
    SYMMETRIC_EXTENT_DIRECTION,
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
    CircularEdgeChamfer,
    DeferredCenterBore,
    FeaturePlan,
    OuterCylinder,
    OrientedRectangleExtrude,
    ParameterBinding,
    PolygonExtrude,
    ProfileExtrude,
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
    # True when connect() started this Inventor process rather than reusing one.
    launched: bool = False

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

        # 1) Reuse an already-running Inventor instance if one exists (fast, avoids
        #    spawning a second copy of the application).
        app = None
        try:
            app = win32_client.GetActiveObject(INVENTOR_PROG_ID)
            INV = getattr(win32_client, "constants", _inventor_fallback_constants())
        except Exception:
            app = None

        launched = app is None
        if app is None:
            # 2) Launch a new instance via the cached type library (gives named constants).
            try:
                app = win32_client.gencache.EnsureDispatch(INVENTOR_PROG_ID)
                INV = win32_client.constants
            except Exception as ensure_exc:
                # 3) Fall back to late-bound dispatch if the gen_py cache is broken/stale;
                #    named constants aren't available here, so use our own fallback enum.
                try:
                    app = win32_client.dynamic.Dispatch(INVENTOR_PROG_ID)
                    INV = _inventor_fallback_constants()
                except Exception as dynamic_exc:
                    raise InventorConnectionError(
                        "Inventor COM connection failed. Make sure Autodesk Inventor is installed. "
                        f"EnsureDispatch error: {ensure_exc}; dynamic Dispatch error: {dynamic_exc}"
                    ) from dynamic_exc

        try:
            # A reused session belongs to the user: it may be shown, never hidden.
            if launched or visible:
                app.Visible = visible
        except Exception as exc:
            raise InventorConnectionError(
                "Connected to Inventor, but could not set visibility. "
                f"Original COM error: {exc}"
            ) from exc

        return cls(app=app, constants=INV, launched=launched)

    def quit_if_launched(self) -> bool:
        """Quit Inventor only if this connection started it; never quit a reused session.

        A hidden Inventor started through COM is not registered for GetActiveObject, so
        later connections cannot reuse it, and it keeps running after Python exits.
        """

        if not self.launched:
            return False
        try:
            self.app.Quit()
        except Exception as exc:
            raise InventorConnectionError(
                f"Could not quit the Inventor instance this connection started. "
                f"Original COM error: {exc}"
            ) from exc
        self.launched = False
        return True

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
        # A center bore is recorded but not cut until ApplyDeferredBores runs, so it can
        # be sized against the smallest outer cylinder joined earlier in the same plan.
        deferred_bore: DeferredCenterBore | None = None
        # One operation may carry several bindings (e.g. a circle's diameter and extent).
        bindings: dict[int, list[ParameterBinding]] = {}
        for binding in plan.parameter_bindings:
            bindings.setdefault(binding.operation_index, []).append(binding)
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
            elif isinstance(operation, ProfileExtrude):
                feature = self._add_profile_extrude(document, operation)
            elif isinstance(operation, Shell):
                feature = self._add_shell(document, operation)
            elif isinstance(operation, CircularEdgeChamfer):
                feature = self._add_circular_edge_chamfer(document, operation)
            for binding in bindings.get(operation_index, []):
                self._bind_feature_parameter(feature, binding.expression, target=binding.target)

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

    def _bind_feature_parameter(
        self,
        feature: Any | None,
        expression: str,
        *,
        target: str = "extent",
    ) -> None:
        if feature is None:
            raise InventorGeometryError(
                f"Could not bind feature {target} to parameter expression {expression!r}."
            )
        if target == "diameter":
            self._bind_sketch_circle_diameter(feature, expression)
            return
        if target == "distance":
            getters = (
                lambda: feature.Definition.Distance,
                lambda: feature.Parameters.Item(1),
            )
        elif target == "extent":
            # With early-bound (gencache) wrappers, ExtrudeFeature.Extent is typed as the
            # PartFeatureExtent base class, which hides Distance until cast.
            getters = (
                lambda: feature.Extent.Distance,
                lambda: _cast_to(feature.Extent, "DistanceExtent").Distance,
                lambda: feature.Definition.Extent.Distance,
                lambda: _cast_to(feature.Definition.Extent, "DistanceExtent").Distance,
                lambda: feature.Definition.Distance,
            )
        else:
            raise InventorPlanError(f"Unsupported parameter target={target!r}.")
        for getter in getters:
            try:
                getter().Expression = expression
                return
            except Exception:
                continue
        raise InventorGeometryError(
            f"Inventor did not expose a {target} parameter for expression {expression!r}."
        )

    def _bind_sketch_circle_diameter(self, feature: Any, expression: str) -> None:
        """Ground the profile circle's center and drive its diameter by an expression."""

        try:
            try:
                sketch = feature.Profile.Parent
            except Exception:
                sketch = feature.Definition.Profile.Parent
            if int(sketch.SketchCircles.Count) != 1:
                raise InventorGeometryError(
                    "A diameter binding needs a profile sketch with exactly one circle."
                )
            circle = sketch.SketchCircles.Item(1)
            sketch.GeometricConstraints.AddGround(circle.CenterSketchPoint)
            center = circle.CenterSketchPoint.Geometry
            text_point = self.app.TransientGeometry.CreatePoint2d(
                center.X + circle.Radius,
                center.Y + circle.Radius,
            )
            dimension = sketch.DimensionConstraints.AddDiameter(circle, text_point)
            dimension.Parameter.Expression = expression
        except InventorGeometryError:
            raise
        except Exception as exc:
            raise InventorGeometryError(
                f"Could not bind sketch circle diameter to {expression!r}. "
                f"Original COM error: {exc}"
            ) from exc

    def save_document(self, document: Any) -> None:
        try:
            document.Save()
        except Exception as exc:
            raise InventorDocumentError(
                f"Could not save the Inventor document. Original COM error: {exc}"
            ) from exc

    def new_assembly_document(self) -> Any:
        try:
            document = self.app.Documents.Add(self._constant("kAssemblyDocumentObject"))
            # Early-bound Documents.Add returns the generic Document interface, which
            # hides ComponentDefinition until cast.
            return _cast_to(document, "AssemblyDocument")
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

    def export_stl(
        self,
        document: Any,
        path: str | Path,
        *,
        resolution: Literal["high", "medium", "low"] = "high",
    ) -> None:
        """Export a binary STL whose coordinates are in millimeters.

        A plain ``SaveAs`` uses whatever units/resolution the STL translator last
        saved, so the translator is driven with explicit options instead. If the
        translator cannot be driven, fall back to ``SaveAs`` and warn.
        """

        stl_path = path_with_suffix("path", Path(path), (STL_SUFFIX,))
        if resolution not in STL_RESOLUTION_VALUES:
            raise InventorPlanError(f"Unsupported STL resolution={resolution!r}.")
        stl_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._export_stl_with_translator(document, stl_path, resolution)
            return
        except Exception as translator_exc:
            warnings.warn(
                "Inventor STL translator options were unavailable; exported with "
                "Document.SaveAs, which uses the translator's last saved units. "
                f"Original COM error: {translator_exc}",
                RuntimeWarning,
                stacklevel=2,
            )
        try:
            document.SaveAs(str(stl_path), True)
        except Exception as exc:
            raise InventorExportError(
                f"Could not export STL to {stl_path}. Original COM error: {exc}"
            ) from exc

    def _export_stl_with_translator(
        self,
        document: Any,
        stl_path: Path,
        resolution: str,
    ) -> None:
        if stl_path.exists():
            stl_path.unlink()
        translator = _cast_to(
            self.app.ApplicationAddIns.ItemById(STL_TRANSLATOR_ADDIN_ID),
            "TranslatorAddIn",
        )
        # An inactive translator accepts SaveCopyAs but silently writes nothing.
        if not translator.Activated:
            translator.Activate()
        transient_objects = self.app.TransientObjects
        context = transient_objects.CreateTranslationContext()
        context.Type = self._optional_constant("kFileBrowseIOMechanism", FILE_BROWSE_IO_MECHANISM)
        options = transient_objects.CreateNameValueMap()
        if not translator.HasSaveCopyAsOptions(document, context, options):
            raise InventorExportError("The STL translator did not provide export options.")
        _set_name_value(options, "ExportUnits", STL_EXPORT_UNITS_MM)
        _set_name_value(options, "Resolution", STL_RESOLUTION_VALUES[resolution])
        _set_name_value(options, "OutputFileType", 0)  # binary
        medium = transient_objects.CreateDataMedium()
        medium.FileName = str(stl_path.resolve())
        translator.SaveCopyAs(document, context, options, medium)
        if not stl_path.exists():
            raise InventorExportError(f"The STL translator did not write {stl_path}.")

    def _add_circular_edge_chamfer(
        self,
        document: Any,
        operation: CircularEdgeChamfer,
    ) -> Any:
        label = "circular edge chamfer"
        try:
            component_definition = document.ComponentDefinition
            radius_cm = mm_to_cm(mm_radius(operation.edge_diameter_mm))
            center_cm = (
                mm_to_cm(operation.x_mm),
                mm_to_cm(operation.y_mm),
                mm_to_cm(operation.z_mm),
            )
            circle_curve = self._optional_constant("kCircleCurve", CIRCLE_CURVE_TYPE)
            tolerance_cm = 1e-5
            edges = self.app.TransientObjects.CreateEdgeCollection()
            bodies = component_definition.SurfaceBodies
            for body_index in range(1, int(bodies.Count) + 1):
                body_edges = bodies.Item(body_index).Edges
                for edge_index in range(1, int(body_edges.Count) + 1):
                    edge = body_edges.Item(edge_index)
                    if int(edge.GeometryType) != circle_curve:
                        continue
                    circle = edge.Geometry
                    center = circle.Center
                    normal = circle.Normal
                    if (
                        abs(float(circle.Radius) - radius_cm) <= tolerance_cm
                        and abs(float(center.X) - center_cm[0]) <= tolerance_cm
                        and abs(float(center.Y) - center_cm[1]) <= tolerance_cm
                        and abs(float(center.Z) - center_cm[2]) <= tolerance_cm
                        and abs(abs(float(normal.Z)) - 1.0) <= 1e-9
                    ):
                        edges.Add(edge)
            if int(edges.Count) == 0:
                raise InventorGeometryError(
                    f"No circular edge of diameter {operation.edge_diameter_mm:g} mm at "
                    f"({operation.x_mm:g}, {operation.y_mm:g}, {operation.z_mm:g}) mm to chamfer."
                )
            feature = component_definition.Features.ChamferFeatures.AddUsingDistance(
                edges,
                mm_to_cm(operation.distance_mm),
            )
            _try_set_attribute(feature, "Name", label)
            return feature
        except InventorGeometryError:
            raise
        except Exception as exc:
            raise InventorGeometryError(
                f"Could not create {label} of {operation.distance_mm:g} mm. "
                f"Original COM error: {exc}"
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
            geometry_points = _rotated_rectangle_points(
                self.app.TransientGeometry,
                operation.x_mm,
                operation.y_mm,
                operation.width_mm,
                operation.height_mm,
                operation.angle_deg,
            )
            points = [sketch.SketchPoints.Add(point) for point in geometry_points]
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
            center_u_mm, center_v_mm, offset_mm = _plane_coordinates(
                operation.plane,
                x_mm=operation.x_mm,
                y_mm=operation.y_mm,
                z_mm=operation.z_mm,
            )
            work_plane = self._work_plane_for_plane(component_definition, operation.plane, offset_mm)
            sketch = component_definition.Sketches.Add(work_plane)
            geometry_points = _polygon_points(
                self.app.TransientGeometry,
                operation.sides,
                operation.circumradius_mm,
                center_u_mm,
                center_v_mm,
                operation.rotation_deg,
            )
            points = [sketch.SketchPoints.Add(point) for point in geometry_points]
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
            geometry_points = _annular_sector_points(
                self.app.TransientGeometry,
                operation.inner_radius_mm,
                operation.outer_radius_mm,
                operation.start_angle_deg,
                operation.end_angle_deg,
            )
            points = [sketch.SketchPoints.Add(point) for point in geometry_points]
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
            _try_set_attribute(feature, "Name", f"annular sector {operation.operation}")
            return feature
        except Exception as exc:
            raise InventorGeometryError(
                "Could not create annular sector. Original COM error: " f"{exc}"
            ) from exc

    def _add_profile_extrude(self, document: Any, operation: ProfileExtrude) -> Any:
        try:
            component_definition = document.ComponentDefinition
            work_plane = self._work_plane_for_plane(
                component_definition,
                operation.plane,
                operation.offset_mm,
            )
            sketch = component_definition.Sketches.Add(work_plane)
            geometry_points = [
                self.app.TransientGeometry.CreatePoint2d(mm_to_cm(x), mm_to_cm(y))
                for x, y in operation.points
            ]
            points = [sketch.SketchPoints.Add(point) for point in geometry_points]
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
            _try_set_attribute(feature, "Name", f"profile {operation.operation}")
            return feature
        except Exception as exc:
            raise InventorGeometryError(
                f"Could not create profile on {operation.plane}. Original COM error: {exc}"
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

    def _optional_constant(self, name: str, default: int) -> int:
        value = getattr(self.constants, name, None)
        return default if value is None else int(value)


def _try_set_attribute(target: Any, name: str, value: object) -> bool:
    try:
        setattr(target, name, value)
    except Exception:
        return False
    return True


def _cast_to(target: Any, interface: str) -> Any:
    """Cast an early-bound COM wrapper to a derived interface; no-op if unavailable."""

    try:
        win32_client = cast(Any, import_module("win32com.client"))
        return win32_client.CastTo(target, interface)
    except Exception:
        return target


def _set_name_value(options: Any, name: str, value: object) -> None:
    """Set an existing entry of an Inventor NameValueMap."""

    try:
        options.SetValue(name, value)
    except AttributeError:
        # Late-bound NameValueMap: Value is a parameterized property, so put it directly.
        pythoncom = cast(Any, import_module("pythoncom"))
        dispid = options._oleobj_.GetIDsOfNames("Value")
        options._oleobj_.Invoke(dispid, 0, pythoncom.DISPATCH_PROPERTYPUT, 0, name, value)


def _inventor_fallback_constants() -> Any:
    """Return the small documented enum subset used by this backend."""

    return SimpleNamespace(
        kPartDocumentObject=PART_DOCUMENT_TYPE,
        kAssemblyDocumentObject=ASSEMBLY_DOCUMENT_TYPE,
        kJoinOperation=JOIN_OPERATION,
        kCutOperation=CUT_OPERATION,
        kPositiveExtentDirection=POSITIVE_EXTENT_DIRECTION,
        kNegativeExtentDirection=NEGATIVE_EXTENT_DIRECTION,
        kSymmetricExtentDirection=SYMMETRIC_EXTENT_DIRECTION,
        kCircleCurve=CIRCLE_CURVE_TYPE,
        kFileBrowseIOMechanism=FILE_BROWSE_IO_MECHANISM,
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


def _annular_sector_points(
    transient_geometry: Any,
    inner_radius_mm: float,
    outer_radius_mm: float,
    start_angle_deg: float,
    end_angle_deg: float,
    segments: int = 64,
) -> list[Any]:
    """Approximate arcs with a fine polygon for reliable Inventor profiles."""

    points = [
        _polar_point(
            transient_geometry,
            outer_radius_mm,
            start_angle_deg + (end_angle_deg - start_angle_deg) * index / segments,
        )
        for index in range(segments + 1)
    ]
    points.extend(
        _polar_point(
            transient_geometry,
            inner_radius_mm,
            end_angle_deg - (end_angle_deg - start_angle_deg) * index / segments,
        )
        for index in range(1, segments)
    )
    return points


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
