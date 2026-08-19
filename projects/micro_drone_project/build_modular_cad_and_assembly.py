"""Build Modular 3D CAD Parts (.IPT), STLs, and Full Assembly (.IAM) in Autodesk Inventor.

Parts Generated:
1. micro_drone_center_deck.ipt & .stl
2. micro_drone_battery_cage.ipt & .stl
3. micro_drone_arm_ducted.ipt & .stl (Single printable modular arm)
4. motor_716_coreless.ipt (Motor model)
5. prop_55mm.ipt (Propeller model)
6. micro_drone_frame_unibody.ipt & .stl (Optional single-piece unibody)
7. micro_drone_assembly.iam (True Inventor Assembly with all occurrences placed)
"""

from pathlib import Path
import math
import sys

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from autodesk_pyinventor.app import connect
from autodesk_pyinventor.part import Part
from autodesk_pyinventor.plan import (
    FeaturePlan,
    PolygonExtrude,
    RectangleExtrude,
    CircleExtrude,
    OrientedRectangleExtrude,
)
from autodesk_pyinventor.units import mm_to_cm

GENERATED_DIR = BASE_DIR / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def plan_center_deck() -> FeaturePlan:
    """Center main deck with RP2040 and MPU-6050 mounting deck and 4 arm joints."""
    ops = [
        PolygonExtrude(
            sides=8,
            circumradius_mm=14.0,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=-3.0,
            length_mm=4.0,
            operation="join",
        ),
        # Weight reduction / wire pass-through center hole
        CircleExtrude(
            diameter_mm=8.0,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=-3.5,
            length_mm=5.0,
            operation="cut",
        ),
    ]
    return FeaturePlan(name="micro_drone_center_deck", operations=ops)


def plan_battery_cage() -> FeaturePlan:
    """Modular bottom slide-in battery cage for 1S LiPo (18.5x8.0mm slot)."""
    ops = [
        RectangleExtrude(
            width_mm=21.0,
            height_mm=10.0,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=-10.0,
            length_mm=7.0,
            operation="join",
        ),
        RectangleExtrude(
            width_mm=18.5,
            height_mm=8.0,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=-10.5,
            length_mm=8.0,
            operation="cut",
        ),
    ]
    return FeaturePlan(name="micro_drone_battery_cage", operations=ops)


def plan_modular_arm(
    arm_length_mm: float = 44.0,
    motor_d_mm: float = 7.05,
    duct_id_mm: float = 57.0,
    duct_wall_t_mm: float = 0.8,
    duct_h_mm: float = 10.0,
) -> FeaturePlan:
    """Single modular arm with stealth duct and 716 motor pod."""
    ops = [
        # Arm Beam along X-axis from x=0 to x=arm_length_mm
        RectangleExtrude(
            width_mm=arm_length_mm,
            height_mm=4.0,
            x_mm=arm_length_mm / 2.0,
            y_mm=0.0,
            z_mm=-2.0,
            length_mm=2.6,
            operation="join",
        ),
        # Motor Pod Outer Cylinder
        CircleExtrude(
            diameter_mm=motor_d_mm + 2.4,
            x_mm=arm_length_mm,
            y_mm=0.0,
            z_mm=-4.0,
            length_mm=17.5,
            operation="join",
        ),
        # Motor Pod Inner Bore
        CircleExtrude(
            diameter_mm=motor_d_mm,
            x_mm=arm_length_mm,
            y_mm=0.0,
            z_mm=-4.5,
            length_mm=18.5,
            operation="cut",
        ),
        # Bottom Lip Cut
        CircleExtrude(
            diameter_mm=6.0,
            x_mm=arm_length_mm,
            y_mm=0.0,
            z_mm=-5.0,
            length_mm=2.0,
            operation="cut",
        ),
        # 8-Sided Stealth Duct Outer
        PolygonExtrude(
            sides=8,
            circumradius_mm=(duct_id_mm / 2.0) + duct_wall_t_mm,
            x_mm=arm_length_mm,
            y_mm=0.0,
            z_mm=0.0,
            length_mm=duct_h_mm,
            operation="join",
        ),
        # 8-Sided Stealth Duct Inner Cut
        PolygonExtrude(
            sides=8,
            circumradius_mm=duct_id_mm / 2.0,
            x_mm=arm_length_mm,
            y_mm=0.0,
            z_mm=-0.5,
            length_mm=duct_h_mm + 1.0,
            operation="cut",
        ),
    ]

    # 3 Struts
    for offset in [0.0, 120.0, 240.0]:
        rad = math.radians(offset)
        sx = arm_length_mm + (duct_id_mm / 4.0) * math.cos(rad)
        sy = (duct_id_mm / 4.0) * math.sin(rad)
        ops.append(
            OrientedRectangleExtrude(
                width_mm=duct_id_mm / 2.0,
                height_mm=1.2,
                x_mm=sx,
                y_mm=sy,
                z_mm=2.0,
                length_mm=1.8,
                angle_deg=offset,
                operation="join",
            )
        )

    return FeaturePlan(name="micro_drone_arm_ducted", operations=ops)


def plan_motor_716() -> FeaturePlan:
    """Dummy 716 Coreless Motor."""
    ops = [
        CircleExtrude(
            diameter_mm=7.0,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=0.0,
            length_mm=16.5,
            operation="join",
        ),
        CircleExtrude(
            diameter_mm=0.8,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=16.5,
            length_mm=5.0,
            operation="join",
        ),
    ]
    return FeaturePlan(name="motor_716_coreless", operations=ops)


def plan_prop_55mm() -> FeaturePlan:
    """Dummy 55mm Propeller."""
    ops = [
        CircleExtrude(
            diameter_mm=4.0,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=0.0,
            length_mm=5.0,
            operation="join",
        ),
        RectangleExtrude(
            width_mm=55.0,
            height_mm=5.0,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=3.0,
            length_mm=1.2,
            operation="join",
        ),
    ]
    return FeaturePlan(name="prop_55mm", operations=ops)


def main():
    print("Connecting to Autodesk Inventor COM API...", flush=True)
    app = connect(visible=True)
    print("Connected to Autodesk Inventor successfully!", flush=True)

    # 1. Build and export modular IPT and STL parts
    plans = [
        (plan_center_deck(), GENERATED_DIR / "micro_drone_center_deck.ipt", GENERATED_DIR / "micro_drone_center_deck.stl"),
        (plan_battery_cage(), GENERATED_DIR / "micro_drone_battery_cage.ipt", GENERATED_DIR / "micro_drone_battery_cage.stl"),
        (plan_modular_arm(), GENERATED_DIR / "micro_drone_arm_ducted.ipt", GENERATED_DIR / "micro_drone_arm_ducted.stl"),
        (plan_motor_716(), GENERATED_DIR / "motor_716_coreless.ipt", None),
        (plan_prop_55mm(), GENERATED_DIR / "prop_55mm.ipt", None),
    ]

    saved_parts = {}
    for plan, ipt_path, stl_path in plans:
        print(f"Building separate part: {ipt_path.name}...", flush=True)
        part = Part.from_plan(app=app, plan=plan, path=ipt_path)
        part.save()
        if stl_path:
            part.export_stl(stl_path)
            print(f"  -> Exported STL: {stl_path.name}", flush=True)
        saved_parts[plan.name] = ipt_path
        print(f"  -> Saved IPT: {ipt_path.name} ({ipt_path.stat().st_size} bytes)", flush=True)

    # 2. Build True Inventor Assembly (.IAM)
    iam_path = GENERATED_DIR / "micro_drone_assembly.iam"
    print(f"\nBuilding True Inventor Assembly: {iam_path.name}...", flush=True)
    
    # Remove existing iam if needed to allow fresh assembly creation
    if iam_path.exists():
        try:
            iam_path.unlink()
        except Exception:
            pass

    asm_doc = app.backend.new_assembly_document()
    import win32com.client
    try:
        asm_doc = win32com.client.CastTo(asm_doc, "AssemblyDocument")
    except Exception:
        pass
    comp_def = asm_doc.ComponentDefinition
    tg = app.raw.TransientGeometry

    # Add Center Deck at origin
    m_center = tg.CreateMatrix()
    comp_def.Occurrences.Add(str(saved_parts["micro_drone_center_deck"].resolve()), m_center)
    print("  + Added Center Deck occurrence", flush=True)

    # Add Battery Cage at (0, 0, 0)
    m_battery = tg.CreateMatrix()
    comp_def.Occurrences.Add(str(saved_parts["micro_drone_battery_cage"].resolve()), m_battery)
    print("  + Added Battery Cage occurrence", flush=True)

    # Add 4 Modular Arms (rotated at 45°, 135°, 225°, 315°)
    arm_radius = 44.0
    angles = [45.0, 135.0, 225.0, 315.0]
    for idx, angle in enumerate(angles, 1):
        # Arm rotation matrix
        m_arm = tg.CreateMatrix()
        m_arm.SetToRotation(math.radians(angle), tg.CreateVector(0, 0, 1), tg.CreatePoint(0, 0, 0))
        comp_def.Occurrences.Add(str(saved_parts["micro_drone_arm_ducted"].resolve()), m_arm)
        print(f"  + Added Arm {idx} (angle={angle} deg)", flush=True)

        # Motor in arm pod
        rad = math.radians(angle)
        mx = arm_radius * math.cos(rad)
        my = arm_radius * math.sin(rad)
        m_motor = tg.CreateMatrix()
        m_motor.SetTranslation(tg.CreateVector(mm_to_cm(mx), mm_to_cm(my), mm_to_cm(-4.0)))
        comp_def.Occurrences.Add(str(saved_parts["motor_716_coreless"].resolve()), m_motor)

        # Prop on motor shaft
        m_prop = tg.CreateMatrix()
        m_prop.SetTranslation(tg.CreateVector(mm_to_cm(mx), mm_to_cm(my), mm_to_cm(13.0)))
        comp_def.Occurrences.Add(str(saved_parts["prop_55mm"].resolve()), m_prop)

    asm_doc.SaveAs(str(iam_path.resolve()), False)
    print(f"\n[OK] Successfully built and saved True Inventor Assembly: {iam_path.name} ({iam_path.stat().st_size} bytes)", flush=True)
    print("[OK] All modular parts (.IPT, .STL) and assembly (.IAM) completed!", flush=True)


if __name__ == "__main__":
    main()
