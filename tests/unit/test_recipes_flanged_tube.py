from __future__ import annotations

import pytest

from autodesk_pyinventor.exceptions import ValidationError
from autodesk_pyinventor.recipes import flanged_tube_plan


def test_flanged_tube_plan_order() -> None:
    plan = flanged_tube_plan(
        od=50,
        id=35,
        length=120,
        flange_od=85,
        flange_thickness=12,
    )

    assert [step.action for step in plan.steps] == [
        "base_cylinder",
        "flange_cylinder",
        "center_bore",
    ]
    assert plan.steps[-1].parameters["deferred"] is True


def test_flanged_tube_rejects_small_flange() -> None:
    with pytest.raises(ValidationError):
        flanged_tube_plan(od=50, id=35, length=120, flange_od=45, flange_thickness=12)


def test_flanged_tube_rejects_too_thick_flange() -> None:
    with pytest.raises(ValidationError):
        flanged_tube_plan(od=50, id=35, length=12, flange_od=85, flange_thickness=20)
