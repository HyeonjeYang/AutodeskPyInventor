"""Export Declarative FeaturePlans and AssemblyPlan for Astronomical Camera Rotator.
"""

from pathlib import Path
import json
import sys

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from build_camera_rotator_cad import (
    plan_bearing_housing_upper,
    plan_bearing_housing_lower,
    plan_rotor_spindle,
    plan_camera_adapter_clamp,
    plan_telescope_adapter_clamp,
    plan_rotor_gt2_pulley,
    plan_stepper_motor_bracket,
    plan_bearing_fit_coupon,
    plan_rotor_fit_coupon,
    plan_adapter_fit_coupon,
)

GENERATED_DIR = BASE_DIR / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def main():
    plans = {
        "bearing_housing_upper_plan.json": plan_bearing_housing_upper(),
        "bearing_housing_lower_plan.json": plan_bearing_housing_lower(),
        "rotor_spindle_plan.json": plan_rotor_spindle(),
        "camera_adapter_clamp_plan.json": plan_camera_adapter_clamp(),
        "telescope_adapter_clamp_plan.json": plan_telescope_adapter_clamp(),
        "rotor_gt2_pulley_plan.json": plan_rotor_gt2_pulley(),
        "stepper_motor_bracket_plan.json": plan_stepper_motor_bracket(),
        "bearing_fit_coupon_plan.json": plan_bearing_fit_coupon(),
        "rotor_fit_coupon_plan.json": plan_rotor_fit_coupon(),
        "adapter_fit_coupon_plan.json": plan_adapter_fit_coupon(),
    }

    for filename, plan in plans.items():
        out_path = GENERATED_DIR / filename
        out_path.write_text(plan.to_json(indent=2), encoding="utf-8")
        print(f"Exported FeaturePlan JSON: {filename} ({len(plan.operations)} operations)", flush=True)

    # Assembly Plan JSON
    assembly_plan = {
        "name": "camera_rotator_assembly",
        "units": "mm",
        "occurrences": [
            {"name": "bearing_housing_lower", "translation": [0.0, 0.0, 0.0], "rotation_deg": [0, 0, 0]},
            {"name": "bearing_housing_upper", "translation": [0.0, 0.0, 0.0], "rotation_deg": [0, 0, 0]},
            {"name": "rotor_spindle", "translation": [0.0, 0.0, -6.0], "rotation_deg": [0, 0, 0]},
            {"name": "rotor_gt2_pulley", "translation": [0.0, 0.0, 26.0], "rotation_deg": [0, 0, 0]},
            {"name": "camera_adapter_clamp", "translation": [0.0, 0.0, 36.0], "rotation_deg": [0, 0, 0]},
            {"name": "telescope_adapter_clamp", "translation": [0.0, 0.0, -12.0], "rotation_deg": [0, 0, 0]},
            {"name": "stepper_motor_bracket", "translation": [0.0, -45.0, 5.0], "rotation_deg": [0, 0, 0]},
        ],
    }
    asm_out = GENERATED_DIR / "camera_rotator_assembly_plan.json"
    asm_out.write_text(json.dumps(assembly_plan, indent=2), encoding="utf-8")
    print(f"Exported AssemblyPlan JSON: camera_rotator_assembly_plan.json ({len(assembly_plan['occurrences'])} occurrences)", flush=True)
    print("\n[OK] All declarative CAD Plans exported successfully!", flush=True)


if __name__ == "__main__":
    main()
