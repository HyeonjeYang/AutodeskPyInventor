from __future__ import annotations

import math
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from autodesk_pyinventor.backend import InventorBackend
from autodesk_pyinventor.exceptions import InventorPlanError, InventorValidationError
from autodesk_pyinventor.plan import (
    CircleExtrude,
    CircularEdgeChamfer,
    FeaturePlan,
    ParameterBinding,
)
from autodesk_pyinventor.recipes import (
    meade_lx50_rear_dust_cap_plan,
    socket_depth_from_port_length,
)


def _envelope(plan: FeaturePlan) -> tuple[float, float, float]:
    outer = plan.operations[0]
    assert isinstance(outer, CircleExtrude)
    return outer.diameter_mm, outer.diameter_mm, outer.length_mm


def test_default_dust_cap_matches_prototype_dimensions() -> None:
    plan = meade_lx50_rear_dust_cap_plan()
    outer, bore, chamfer = plan.operations

    assert plan.name == "meade_lx50_rear_dust_cap"
    assert _envelope(plan) == pytest.approx((57.15, 57.15, 11.50))
    assert isinstance(outer, CircleExtrude) and outer.operation == "join"
    assert outer.direction == "negative" and outer.z_mm == 0
    assert isinstance(bore, CircleExtrude) and bore.operation == "cut"
    assert (bore.diameter_mm, bore.length_mm, bore.direction) == (51.60, 9.00, "negative")
    assert isinstance(chamfer, CircularEdgeChamfer)
    assert (chamfer.edge_diameter_mm, chamfer.z_mm, chamfer.distance_mm) == (51.60, 0, 0.75)
    assert chamfer.edge_diameter_mm + 2 * chamfer.distance_mm == pytest.approx(53.10)
    assert outer.length_mm - bore.length_mm == pytest.approx(2.50)
    assert plan.parameters == pytest.approx(
        {
            "bore_id_mm": 51.60,
            "socket_depth_mm": 9.00,
            "cap_od_mm": 57.15,
            "end_wall_mm": 2.50,
            "entry_chamfer_mm": 0.75,
            "thread_od_mm": 50.80,
            "tape_width_mm": 10.0,
            "tape_depth_mm": 4.0,
            "tape_inset_mm": 1.0,
        }
    )


def test_bore_and_socket_depth_are_independent() -> None:
    wider = meade_lx50_rear_dust_cap_plan(bore_id_mm=51.80)
    deeper = meade_lx50_rear_dust_cap_plan(socket_depth_mm=10.25)

    assert wider.operations[1].diameter_mm == 51.80  # type: ignore[union-attr]
    assert wider.operations[1].length_mm == 9.00  # type: ignore[union-attr]
    assert _envelope(wider)[2] == pytest.approx(11.50)
    assert deeper.operations[1].diameter_mm == 51.60  # type: ignore[union-attr]
    assert deeper.operations[1].length_mm == 10.25  # type: ignore[union-attr]
    assert _envelope(deeper)[2] == pytest.approx(12.75)


def test_socket_depth_from_measured_port_adds_one_millimeter() -> None:
    depth = socket_depth_from_port_length(8.4)

    assert depth == pytest.approx(9.4)
    assert socket_depth_from_port_length(8.4, clearance=1.5) == pytest.approx(9.9)
    plan = meade_lx50_rear_dust_cap_plan(socket_depth_mm=depth)
    assert plan.operations[1].length_mm == pytest.approx(9.4)  # type: ignore[union-attr]


def test_bindings_drive_ipt_user_parameters() -> None:
    plan = meade_lx50_rear_dust_cap_plan()

    assert [(b.operation_index, b.target, b.expression) for b in plan.parameter_bindings] == [
        (0, "diameter", "cap_od_mm"),
        (0, "extent", "end_wall_mm + socket_depth_mm"),
        (1, "diameter", "bore_id_mm"),
        (1, "extent", "socket_depth_mm"),
        (2, "distance", "entry_chamfer_mm"),
    ]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"bore_id_mm": 50.80}, "thread_od_mm"),
        ({"socket_depth_mm": 4.9}, "tape zone"),
        ({"entry_chamfer_mm": 1.2}, "tape_inset_mm"),
        ({"cap_od_mm": 53.10}, "entry chamfer"),
        ({"tape_pad_count": 0}, "tape_pad_count"),
        ({"tape_pad_count": 17}, "do not fit"),
    ],
)
def test_dust_cap_rejects_inconsistent_dimensions(kwargs: dict[str, Any], message: str) -> None:
    with pytest.raises(InventorValidationError, match=message):
        meade_lx50_rear_dust_cap_plan(**kwargs)


def test_tape_zone_sits_on_straight_bore_wall() -> None:
    plan = meade_lx50_rear_dust_cap_plan()
    params = plan.parameters

    zone_top = params["tape_inset_mm"]
    zone_bottom = params["tape_inset_mm"] + params["tape_depth_mm"]
    assert params["entry_chamfer_mm"] <= zone_top < zone_bottom <= params["socket_depth_mm"]
    pad_arc_deg = math.degrees(params["tape_width_mm"] / (params["bore_id_mm"] / 2))
    assert pad_arc_deg < 120


def test_dust_cap_plan_round_trips_json_and_explains_chamfer() -> None:
    plan = meade_lx50_rear_dust_cap_plan()

    restored = FeaturePlan.from_json(plan.to_json())

    assert restored == plan
    assert plan.to_dict()["operations"][2] == {  # type: ignore[index]
        "type": "circular_edge_chamfer",
        "edge_diameter": 51.6,
        "x": 0,
        "y": 0,
        "z": 0,
        "distance": 0.75,
    }
    assert "chamfer_circular_edge(diameter=51.6, center=(0,0,0), distance=0.75)" in plan.explain()


def test_plan_rejects_binding_target_that_does_not_fit_operation() -> None:
    with pytest.raises(InventorPlanError, match="cannot bind"):
        FeaturePlan(
            name="bad",
            operations=[
                CircleExtrude(
                    diameter_mm=20, x_mm=0, y_mm=0, z_mm=0, length_mm=5, operation="join"
                ),
                CircularEdgeChamfer(edge_diameter_mm=20, z_mm=5, distance_mm=1),
            ],
            parameter_bindings=[ParameterBinding(1, "diameter", "d")],
        )


def test_chamfer_requires_preceding_solid() -> None:
    with pytest.raises(InventorPlanError, match="preceding solid"):
        FeaturePlan(
            name="bad",
            operations=[CircularEdgeChamfer(edge_diameter_mm=20, z_mm=0, distance_mm=1)],
        )


def test_backend_applies_every_binding_of_one_operation(monkeypatch: pytest.MonkeyPatch) -> None:
    backend = InventorBackend(app=object(), constants=SimpleNamespace())
    calls: list[tuple[str, str]] = []
    monkeypatch.setattr(backend, "_add_user_parameters", lambda document, parameters: None)
    monkeypatch.setattr(backend, "_add_circle_extrude", lambda document, operation: "extrude")
    monkeypatch.setattr(
        backend, "_add_circular_edge_chamfer", lambda document, operation: "chamfer"
    )
    monkeypatch.setattr(
        backend,
        "_bind_feature_parameter",
        lambda feature, expression, *, target: calls.append((target, expression)),
    )

    backend.execute_plan(object(), meade_lx50_rear_dust_cap_plan())

    assert calls == [
        ("diameter", "cap_od_mm"),
        ("extent", "end_wall_mm + socket_depth_mm"),
        ("diameter", "bore_id_mm"),
        ("extent", "socket_depth_mm"),
        ("distance", "entry_chamfer_mm"),
    ]


class _FakeOptions:
    def __init__(self) -> None:
        self.values: dict[str, object] = {"ExportUnits": 2, "Resolution": 4, "OutputFileType": 1}

    def SetValue(self, name: str, value: object) -> None:  # noqa: N802 - COM name
        assert name in self.values
        self.values[name] = value


class _FakeTranslator:
    def __init__(self, *, fail: bool = False) -> None:
        self.Activated = False
        self.fail = fail
        self.options: _FakeOptions | None = None

    def Activate(self) -> None:  # noqa: N802 - COM name
        self.Activated = True

    def HasSaveCopyAsOptions(self, document: object, context: object, options: Any) -> bool:  # noqa: N802
        self.options = options
        return True

    def SaveCopyAs(self, document: object, context: object, options: Any, medium: Any) -> None:  # noqa: N802
        if self.fail or not self.Activated:
            return
        Path(medium.FileName).write_bytes(b"\0" * 84)


def _fake_app(translator: _FakeTranslator) -> Any:
    return SimpleNamespace(
        ApplicationAddIns=SimpleNamespace(ItemById=lambda _id: translator),
        TransientObjects=SimpleNamespace(
            CreateTranslationContext=lambda: SimpleNamespace(Type=None),
            CreateNameValueMap=_FakeOptions,
            CreateDataMedium=lambda: SimpleNamespace(FileName=""),
        ),
    )


def test_export_stl_forces_millimeters_and_high_resolution(tmp_path: Path) -> None:
    translator = _FakeTranslator()
    backend = InventorBackend(app=_fake_app(translator), constants=SimpleNamespace())

    backend.export_stl(object(), tmp_path / "cap.stl")

    assert (tmp_path / "cap.stl").exists()
    assert translator.Activated
    assert translator.options is not None
    assert translator.options.values == {"ExportUnits": 5, "Resolution": 0, "OutputFileType": 0}


def test_export_stl_warns_and_falls_back_to_save_as(tmp_path: Path) -> None:
    translator = _FakeTranslator(fail=True)
    backend = InventorBackend(app=_fake_app(translator), constants=SimpleNamespace())
    saved: list[str] = []
    document = SimpleNamespace(SaveAs=lambda path, copy: saved.append(path))

    with pytest.warns(RuntimeWarning, match="SaveAs"):
        backend.export_stl(document, tmp_path / "cap.stl")

    assert saved == [str(tmp_path / "cap.stl")]
