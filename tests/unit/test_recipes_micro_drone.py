"""Unit tests for micro drone frame recipe."""

from autodesk_pyinventor.recipes import micro_drone_frame_plan


def test_micro_drone_frame_plan_default():
    plan = micro_drone_frame_plan()
    assert plan.name == "micro_drone_frame"
    assert len(plan.operations) > 30
    assert plan.parameters["wb"] == 88.0
    assert plan.parameters["motorD"] == 7.05
    assert plan.parameters["ductID"] == 57.0


def test_micro_drone_frame_plan_custom_wheelbase():
    plan = micro_drone_frame_plan(wheelbase=65.0, motor_d=7.0, duct_id=40.0)
    assert plan.parameters["wb"] == 65.0
    assert plan.parameters["motorD"] == 7.0
    assert plan.parameters["ductID"] == 40.0
