from __future__ import annotations

from autodesk_pyinventor.plan import (
    AnnularSectorExtrude,
    MultiPartPlan,
    PolygonExtrude,
    ProfileExtrude,
    OrientedRectangleExtrude,
)
from autodesk_pyinventor.recipes import (
    astro_controller_accessory_plans,
    astro_kit_addon_plans,
    barn_door_star_tracker_plans,
)


def test_accessory_plan_contains_c_d_and_e_parts() -> None:
    plan = astro_controller_accessory_plans()

    assert isinstance(plan, MultiPartPlan)
    assert set(plan.parts) == {
        "dew_heater_strap_holder",
        "encoder_knob",
        "tripod_mount_belt_clip",
    }
    assert isinstance(plan.parts["dew_heater_strap_holder"].operations[0], AnnularSectorExtrude)
    assert any(isinstance(operation, PolygonExtrude) for operation in plan.parts["tripod_mount_belt_clip"].operations)


def test_barn_door_plan_contains_t1_through_t4() -> None:
    plan = barn_door_star_tracker_plans()

    assert set(plan.parts) == {
        "barn_door_t1_base_board",
        "barn_door_t2_top_board",
        "barn_door_t3_drive_nut_block",
        "barn_door_t4_stepper_coupler",
    }
    assert plan.parameters["L"] == 200
    assert plan.parameters["rodPitch"] == 0.7


def test_astro_kit_plan_contains_f_through_i_parts() -> None:
    plan = astro_kit_addon_plans()

    assert set(plan.parts) == {
        "bahtinov_focusing_mask",
        "dew_shield_lens_hood",
        "power_bank_cradle",
        "tripod_leg_clip",
        "cable_clip",
        "arca_swiss_qr_plate",
    }
    assert isinstance(plan.parts["arca_swiss_qr_plate"].operations[0], ProfileExtrude)
    assert plan.parameters["topW"] == 38


def test_bahtinov_slits_stay_in_separate_regions() -> None:
    from autodesk_pyinventor.recipes import bahtinov_focusing_mask_plan

    operations = [
        operation
        for operation in bahtinov_focusing_mask_plan().operations
        if isinstance(operation, OrientedRectangleExtrude)
    ]

    assert all(operation.y_mm < -0.6 for operation in operations if operation.angle_deg == 0)
    assert all(
        operation.x_mm < 0 and operation.y_mm > 0
        for operation in operations
        if operation.angle_deg == 20
    )
    assert all(
        operation.x_mm > 0 and operation.y_mm > 0
        for operation in operations
        if operation.angle_deg == -20
    )
