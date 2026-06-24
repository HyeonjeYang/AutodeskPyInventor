from __future__ import annotations

import pytest

from autodesk_pyinventor.exceptions import ValidationError
from autodesk_pyinventor.recipes import tube_plan


def test_tube_plan_order() -> None:
    plan = tube_plan(od=50, id=35, length=120)

    assert [step.action for step in plan.steps] == ["base_cylinder", "center_bore"]
    assert plan.metadata["recipe"] == "tube"


def test_tube_rejects_inner_diameter_larger_than_outer() -> None:
    with pytest.raises(ValidationError):
        tube_plan(od=50, id=60, length=120)
