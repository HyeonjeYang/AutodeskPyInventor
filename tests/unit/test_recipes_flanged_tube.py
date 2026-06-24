from __future__ import annotations

import pytest

from autodesk_pyinventor.exceptions import ValidationError
from autodesk_pyinventor.recipes import flanged_tube_plan


def test_flanged_tube_joins_outer_solids_before_one_final_bore() -> None:
    plan = flanged_tube_plan(
        body_od=63.5,
        body_id=56.5,
        body_length=236,
        flange_od=90,
        flange_thickness=8,
        flange_z=0,
    )

    assert [operation.to_dict()["type"] for operation in plan.operations] == [
        "outer_cylinder",
        "outer_cylinder",
        "deferred_center_bore",
        "apply_deferred_bores",
    ]
    assert plan.operations[1].to_dict() == {
        "type": "outer_cylinder",
        "diameter": 90,
        "z": 0,
        "length": 8,
    }


def test_flanged_tube_rejects_small_flange() -> None:
    with pytest.raises(ValidationError, match="flange_od=45"):
        flanged_tube_plan(
            body_od=50,
            body_id=35,
            body_length=120,
            flange_od=45,
            flange_thickness=12,
        )


def test_flanged_tube_rejects_bad_body_length() -> None:
    with pytest.raises(ValidationError, match="body_length=-12"):
        flanged_tube_plan(
            body_od=50,
            body_id=35,
            body_length=-12,
            flange_od=85,
            flange_thickness=20,
        )
