from __future__ import annotations

import json

import pytest

from autodesk_pyinventor.exceptions import InventorPlanError, ValidationError
from autodesk_pyinventor.plan import (
    ApplyDeferredBores,
    DeferredCenterBore,
    FeaturePlan,
    OuterCylinder,
)
from autodesk_pyinventor.recipes import disk_plan, tube_plan


def test_feature_plan_round_trips_json() -> None:
    plan = disk_plan(od=80, id=25, thickness=8, name="washer")

    restored = FeaturePlan.from_json(plan.to_json())

    assert restored == plan
    assert json.loads(restored.to_json())["name"] == "washer"


def test_operations_serialize_to_expected_shape() -> None:
    plan = disk_plan(od=80, id=25, thickness=8, name="washer")

    assert plan.to_dict() == {
        "name": "washer",
        "units": "mm",
        "operations": [
            {"type": "outer_cylinder", "diameter": 80, "z": 0, "length": 8},
            {"type": "deferred_center_bore", "diameter": 25, "axis": "Z"},
            {"type": "apply_deferred_bores"},
        ],
    }


def test_plan_rejects_bore_without_apply() -> None:
    with pytest.raises(InventorPlanError):
        FeaturePlan(
            name="bad",
            operations=[
                OuterCylinder(diameter_mm=80, z_mm=0, length_mm=8),
                DeferredCenterBore(diameter_mm=25),
            ],
        )


def test_plan_rejects_outer_cylinder_after_deferred_bore() -> None:
    with pytest.raises(InventorPlanError):
        FeaturePlan(
            name="bad",
            operations=[
                OuterCylinder(diameter_mm=80, z_mm=0, length_mm=8),
                DeferredCenterBore(diameter_mm=25),
                ApplyDeferredBores(),
                OuterCylinder(diameter_mm=90, z_mm=0, length_mm=4),
            ],
        )


def test_plan_append_keeps_operation_order() -> None:
    base = FeaturePlan(name="part")
    combined = base.append_plan(disk_plan(od=80, thickness=8)).append_plan(
        tube_plan(od=50, id=25, length=60)
    )

    assert [operation.to_dict()["type"] for operation in combined.operations] == [
        "outer_cylinder",
        "outer_cylinder",
        "deferred_center_bore",
        "apply_deferred_bores",
    ]


def test_plan_rejects_invalid_operation_dimensions() -> None:
    with pytest.raises(ValidationError, match="diameter_mm=-1"):
        OuterCylinder(diameter_mm=-1, z_mm=0, length_mm=8)


def test_explain_is_human_readable_and_deterministic() -> None:
    plan = disk_plan(od=80, id=25, thickness=8, name="washer")

    assert plan.explain(path=r"C:\temp\washer.ipt") == "\n".join(
        [
            "FeaturePlan: washer",
            "units: mm",
            "operations:",
            '  1. create_part_document(path="C:/temp/washer.ipt", template="standard.ipt")',
            '  2. sketch_circle(plane="XY", z=0, diameter=80)',
            "  3. extrude_join(distance=8)",
            '  4. defer_bore(diameter=25, axis="Z")',
            '  5. apply_center_bore_once(diameter=25, extent="through_all_symmetric")',
            "  6. save()",
        ]
    )
