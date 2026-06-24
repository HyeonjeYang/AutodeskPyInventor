from __future__ import annotations

import pytest

from autodesk_pyinventor.exceptions import ValidationError
from autodesk_pyinventor.plan import FeaturePlan
from autodesk_pyinventor.recipes import disk_plan, washer_plan


def _operation_types(plan: FeaturePlan) -> list[str]:
    return [operation.to_dict()["type"] for operation in plan.operations]


def test_disk_without_hole_has_one_outer_cylinder() -> None:
    plan = disk_plan(od=80, thickness=8)

    assert _operation_types(plan) == ["outer_cylinder"]


def test_disk_with_hole_defers_and_applies_bore_once() -> None:
    plan = disk_plan(od=80, id=25, thickness=8)

    assert _operation_types(plan) == [
        "outer_cylinder",
        "deferred_center_bore",
        "apply_deferred_bores",
    ]


def test_washer_recipe_requires_valid_inner_diameter() -> None:
    with pytest.raises(ValidationError, match="id=25"):
        washer_plan(od=25, id=25, thickness=8)
