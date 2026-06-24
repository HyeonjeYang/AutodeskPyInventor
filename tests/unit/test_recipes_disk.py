from __future__ import annotations

import pytest

from autodesk_pyinventor.exceptions import ValidationError
from autodesk_pyinventor.recipes import disk_plan, washer_plan


def test_disk_without_hole_has_one_step() -> None:
    plan = disk_plan(od=80, thickness=8)

    assert [step.action for step in plan.steps] == ["base_cylinder"]


def test_disk_with_hole_defers_bore() -> None:
    plan = disk_plan(od=80, id=25, thickness=8)

    assert [step.action for step in plan.steps] == ["base_cylinder", "center_bore"]
    assert plan.steps[1].parameters["deferred"] is True


def test_washer_recipe_requires_valid_inner_diameter() -> None:
    with pytest.raises(ValidationError):
        washer_plan(od=25, id=25, thickness=8)
