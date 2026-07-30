from __future__ import annotations

import json

import pytest

from autodesk_pyinventor.exceptions import InventorPlanError, InventorValidationError
from autodesk_pyinventor.plan import (
    CircleExtrude,
    EnclosurePlan,
    FeaturePlan,
    RectangleExtrude,
    Shell,
)
from autodesk_pyinventor.recipes import astro_controller_enclosure_plan


def test_astro_controller_plan_contains_base_and_lid_operations() -> None:
    plan = astro_controller_enclosure_plan()

    assert isinstance(plan, EnclosurePlan)
    assert len(plan.base.operations) == 29
    assert len(plan.lid.operations) == 12
    assert isinstance(plan.base.operations[0], RectangleExtrude)
    assert isinstance(plan.base.operations[1], Shell)
    assert isinstance(plan.lid.operations[0], RectangleExtrude)


def test_astro_controller_plan_serializes_and_round_trips() -> None:
    plan = astro_controller_enclosure_plan()

    restored = EnclosurePlan.from_dict(json.loads(plan.to_json()))

    assert restored == plan
    assert restored.parameters["fit"] == 0.3


def test_astro_controller_user_parameters_use_inventor_names_and_mm_units() -> None:
    plan = astro_controller_enclosure_plan()
    expected = {
        "wall",
        "outX",
        "outY",
        "baseH",
        "lidT",
        "bossH",
        "fit",
        "oledWindowWidth",
        "oledWindowHeight",
        "oledWindowX",
        "oledWindowY",
        "oledPocketSize",
        "oledPocketDepth",
        "encoderHoleDiameter",
    }

    assert plan.units == "mm"
    assert set(plan.parameters) == expected
    assert plan.base.parameters == plan.parameters
    assert plan.lid.parameters == plan.parameters
    assert {binding.expression for binding in plan.base.parameter_bindings} >= {
        "baseH",
        "baseH - wall",
        "bossH",
        "wall",
    }
    assert {binding.expression for binding in plan.lid.parameter_bindings} >= {
        "lidT",
        "oledPocketDepth",
    }


def test_astro_controller_side_cuts_use_explicit_planes_and_directions() -> None:
    plan = astro_controller_enclosure_plan()

    side_cuts = [
        operation
        for operation in plan.base.operations
        if isinstance(operation, (RectangleExtrude, CircleExtrude))
        and operation.operation == "cut"
        and operation.plane != "XY"
    ]

    assert [(operation.plane, operation.direction) for operation in side_cuts] == [
        ("YZ", "negative"),
        ("XZ", "positive"),
        ("YZ", "positive"),
    ]


def test_astro_controller_rejects_pocket_that_reaches_through_lid() -> None:
    with pytest.raises(InventorValidationError, match="oled_pocket_depth"):
        astro_controller_enclosure_plan(oled_pocket_depth=3.0)


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"wall": 0}, "wall"),
        ({"fit": -0.1}, "fit"),
        ({"oled_window_x": 1}, "OLED window"),
        ({"oled_window_y": 57}, "OLED window"),
    ],
)
def test_astro_controller_rejects_invalid_fit_critical_geometry(
    kwargs: dict[str, float],
    message: str,
) -> None:
    with pytest.raises(InventorValidationError, match=message):
        astro_controller_enclosure_plan(**kwargs)


def test_feature_plan_rejects_cut_before_first_solid() -> None:
    with pytest.raises(InventorPlanError, match="preceding solid"):
        FeaturePlan(
            name="invalid",
            operations=[
                RectangleExtrude(
                    width_mm=10,
                    height_mm=10,
                    x_mm=5,
                    y_mm=5,
                    z_mm=0,
                    length_mm=1,
                    operation="cut",
                )
            ],
        )
