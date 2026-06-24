from __future__ import annotations

import pytest

from autodesk_pyinventor.exceptions import ValidationError
from autodesk_pyinventor.recipes import tube_plan


def test_tube_plan_order() -> None:
    plan = tube_plan(od=63.5, id=56.5, length=236)

    assert [operation.to_dict()["type"] for operation in plan.operations] == [
        "outer_cylinder",
        "deferred_center_bore",
        "apply_deferred_bores",
    ]
    assert plan.operations[0].to_dict() == {
        "type": "outer_cylinder",
        "diameter": 63.5,
        "z": 0,
        "length": 236,
    }


def test_tube_rejects_inner_diameter_larger_than_outer() -> None:
    with pytest.raises(ValidationError, match="id=60"):
        tube_plan(od=50, id=60, length=120)
