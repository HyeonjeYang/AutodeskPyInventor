"""Build Modular 3D CAD Parts (.IPT), STLs, and Full Assembly (.IAM) for Astronomical Camera Rotator.

Parts Generated:
1. bearing_housing_upper.ipt & .stl (Upper clamshell half)
2. bearing_housing_lower.ipt & .stl (Lower clamshell half)
3. rotor_spindle.ipt & .stl (Hollow optical rotor, 44mm clear aperture)
4. camera_adapter_clamp.ipt & .stl (Split clamp for metal camera adapter)
5. telescope_adapter_clamp.ipt & .stl (Split clamp for telescope adapter)
6. rotor_gt2_pulley.ipt & .stl (120T GT2 timing pulley)
7. stepper_motor_bracket.ipt & .stl (NEMA14/17 bracket with tension slots)
8. bearing_fit_coupon.ipt & .stl (Fit calibration coupon for 65mm bearing)
9. rotor_fit_coupon.ipt & .stl (Fit calibration coupon for 50mm rotor)
10. adapter_fit_coupon.ipt & .stl (Fit calibration coupon for 54mm adapter)
11. camera_rotator_assembly.iam (True Inventor Assembly with all occurrences)
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


# --- 1. Fixed Bearing Housing (Upper & Lower Clamshell) ---

def plan_bearing_housing_upper(
    housing_od_mm: float = 78.0,
    bearing_bore_mm: float = 65.20,
    bearing_w_mm: float = 7.0,
    bearing_spacing_mm: float = 22.0,
    total_length_mm: float = 38.0,
) -> FeaturePlan:
    """Upper clamshell half of the fixed bearing housing with 6x M4 bolt bosses."""
    ops = [
        # Outer Semi-Cylinder Body (Upper half, Y >= 0)
        RectangleExtrude(
            width_mm=housing_od_mm,
            height_mm=housing_od_mm / 2.0,
            x_mm=0.0,
            y_mm=housing_od_mm / 4.0,
            z_mm=0.0,
            length_mm=total_length_mm,
            operation="join",
        ),
        # Central Optical Clearance Cut (52mm ID)
        CircleExtrude(
            diameter_mm=52.0,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=-0.5,
            length_mm=total_length_mm + 1.0,
            operation="cut",
        ),
        # Front Bearing Pocket (65.20mm ID, width 7.5mm)
        CircleExtrude(
            diameter_mm=bearing_bore_mm,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=-0.1,
            length_mm=bearing_w_mm + 0.5,
            operation="cut",
        ),
        # Rear Bearing Pocket (65.20mm ID, width 7.5mm at Z = spacing)
        CircleExtrude(
            diameter_mm=bearing_bore_mm,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=bearing_spacing_mm,
            length_mm=bearing_w_mm + 0.5,
            operation="cut",
        ),
        # Left Flange M4 Bolt Holes (3x M4 clearance 4.4mm)
        CircleExtrude(diameter_mm=4.4, x_mm=-34.0, y_mm=6.0, z_mm=-0.5, length_mm=total_length_mm + 1.0, operation="cut"),
        # Right Flange M4 Bolt Holes (3x M4 clearance 4.4mm)
        CircleExtrude(diameter_mm=4.4, x_mm=34.0, y_mm=6.0, z_mm=-0.5, length_mm=total_length_mm + 1.0, operation="cut"),
    ]
    return FeaturePlan(name="bearing_housing_upper", operations=ops)


def plan_bearing_housing_lower(
    housing_od_mm: float = 78.0,
    bearing_bore_mm: float = 65.20,
    bearing_w_mm: float = 7.0,
    bearing_spacing_mm: float = 22.0,
    total_length_mm: float = 38.0,
) -> FeaturePlan:
    """Lower clamshell half of the fixed bearing housing with motor bracket mount."""
    ops = [
        # Outer Semi-Cylinder Body (Lower half, Y <= 0)
        RectangleExtrude(
            width_mm=housing_od_mm,
            height_mm=housing_od_mm / 2.0,
            x_mm=0.0,
            y_mm=-housing_od_mm / 4.0,
            z_mm=0.0,
            length_mm=total_length_mm,
            operation="join",
        ),
        # Motor Bracket Mounting Boss on bottom
        RectangleExtrude(
            width_mm=40.0,
            height_mm=12.0,
            x_mm=0.0,
            y_mm=-housing_od_mm / 2.0 - 6.0,
            z_mm=5.0,
            length_mm=total_length_mm - 10.0,
            operation="join",
        ),
        # Central Optical Clearance Cut (52mm ID)
        CircleExtrude(
            diameter_mm=52.0,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=-0.5,
            length_mm=total_length_mm + 1.0,
            operation="cut",
        ),
        # Front Bearing Pocket (65.20mm ID)
        CircleExtrude(
            diameter_mm=bearing_bore_mm,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=-0.1,
            length_mm=bearing_w_mm + 0.5,
            operation="cut",
        ),
        # Rear Bearing Pocket (65.20mm ID)
        CircleExtrude(
            diameter_mm=bearing_bore_mm,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=bearing_spacing_mm,
            length_mm=bearing_w_mm + 0.5,
            operation="cut",
        ),
        # Flange M4 Holes with Hex Nut Pockets
        CircleExtrude(diameter_mm=4.4, x_mm=-34.0, y_mm=-6.0, z_mm=-0.5, length_mm=total_length_mm + 1.0, operation="cut"),
        CircleExtrude(diameter_mm=4.4, x_mm=34.0, y_mm=-6.0, z_mm=-0.5, length_mm=total_length_mm + 1.0, operation="cut"),
    ]
    return FeaturePlan(name="bearing_housing_lower", operations=ops)


# --- 2. Rotating Spindle / Rotor ---

def plan_rotor_spindle(
    rotor_od_mm: float = 49.90,
    optical_id_mm: float = 44.0,
    flange_od_mm: float = 68.0,
    total_length_mm: float = 50.0,
) -> FeaturePlan:
    """Hollow optical rotor spindle passing through 2 bearings, with GT2 pulley mounting flange."""
    ops = [
        # Main Spindle Body (49.90mm OD)
        CircleExtrude(
            diameter_mm=rotor_od_mm,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=0.0,
            length_mm=total_length_mm,
            operation="join",
        ),
        # GT2 Pulley Mounting Flange (68mm OD, 4mm thick at Z=32mm)
        CircleExtrude(
            diameter_mm=flange_od_mm,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=32.0,
            length_mm=4.0,
            operation="join",
        ),
        # Front Camera Shoulder (54mm OD for clamp engagement)
        CircleExtrude(
            diameter_mm=54.0,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=36.0,
            length_mm=14.0,
            operation="join",
        ),
        # Clear Optical Path Through-All Bore (44.0mm ID)
        CircleExtrude(
            diameter_mm=optical_id_mm,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=-0.5,
            length_mm=total_length_mm + 1.0,
            operation="cut",
        ),
    ]
    # 6x M3 Bolt Holes on Flange (PCD 58mm)
    for i in range(6):
        rad = math.radians(i * 60.0)
        bx = 29.0 * math.cos(rad)
        by = 29.0 * math.sin(rad)
        ops.append(
            CircleExtrude(
                diameter_mm=3.2,
                x_mm=bx,
                y_mm=by,
                z_mm=31.5,
                length_mm=5.0,
                operation="cut",
            )
        )
    return FeaturePlan(name="rotor_spindle", operations=ops)


# --- 3. Camera & Telescope Adapter Clamps ---

def plan_camera_adapter_clamp(
    adapter_od_mm: float = 54.0,
    clearance_mm: float = 0.20,
    clamp_w_mm: float = 12.0,
) -> FeaturePlan:
    """Split clamp for standard metal M42/M48/NEX camera adapters."""
    bore = adapter_od_mm + clearance_mm  # 54.20mm
    outer_od = bore + 10.0  # 64.20mm
    ops = [
        # Outer Ring
        CircleExtrude(
            diameter_mm=outer_od,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=0.0,
            length_mm=clamp_w_mm,
            operation="join",
        ),
        # Clamping Ears Boss
        RectangleExtrude(
            width_mm=16.0,
            height_mm=18.0,
            x_mm=outer_od / 2.0 + 4.0,
            y_mm=0.0,
            z_mm=0.0,
            length_mm=clamp_w_mm,
            operation="join",
        ),
        # Inner Adapter Bore Cut
        CircleExtrude(
            diameter_mm=bore,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=-0.5,
            length_mm=clamp_w_mm + 1.0,
            operation="cut",
        ),
        # Split Slit (1.5mm gap)
        RectangleExtrude(
            width_mm=25.0,
            height_mm=1.5,
            x_mm=outer_od / 2.0 + 5.0,
            y_mm=0.0,
            z_mm=-0.5,
            length_mm=clamp_w_mm + 1.0,
            operation="cut",
        ),
        # M4 Clamping Bolt Hole (4.4mm)
        CircleExtrude(
            diameter_mm=4.4,
            x_mm=outer_od / 2.0 + 5.0,
            y_mm=0.0,
            z_mm=clamp_w_mm / 2.0,
            length_mm=18.0,
            plane="XZ",
            operation="cut",
        ),
    ]
    return FeaturePlan(name="camera_adapter_clamp", operations=ops)


def plan_telescope_adapter_clamp() -> FeaturePlan:
    """Split clamp for telescope-side metal adapter."""
    plan = plan_camera_adapter_clamp(adapter_od_mm=54.0, clearance_mm=0.20, clamp_w_mm=12.0)
    return FeaturePlan(name="telescope_adapter_clamp", operations=plan.operations)


# --- 4. Large GT2 Pulley ---

def plan_rotor_gt2_pulley(
    teeth: int = 120,
    pitch_mm: float = 2.0,
    belt_w_mm: float = 6.0,
    bore_mm: float = 50.0,
) -> FeaturePlan:
    """120T GT2 Timing Pulley (PCD ~76.39mm, OD ~75.88mm) with 6x M3 bolt mounting holes."""
    pitch_dia = (teeth * pitch_mm) / math.pi  # 76.394 mm
    outer_dia = pitch_dia - 0.508  # 75.88 mm
    flange_dia = outer_dia + 4.0  # 79.88 mm
    pulley_w = belt_w_mm + 2.0  # 8.0 mm

    ops = [
        # Main Pulley Body
        CircleExtrude(
            diameter_mm=outer_dia,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=0.0,
            length_mm=pulley_w,
            operation="join",
        ),
        # Outer Flange (prevents belt walk)
        CircleExtrude(
            diameter_mm=flange_dia,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=0.0,
            length_mm=1.2,
            operation="join",
        ),
        # Inner Flange
        CircleExtrude(
            diameter_mm=flange_dia,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=pulley_w - 1.2,
            length_mm=1.2,
            operation="join",
        ),
        # Center Rotor Clearance Bore
        CircleExtrude(
            diameter_mm=bore_mm,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=-0.5,
            length_mm=pulley_w + 1.0,
            operation="cut",
        ),
    ]
    # 6x M3 Bolt Holes (PCD 58mm)
    for i in range(6):
        rad = math.radians(i * 60.0)
        bx = 29.0 * math.cos(rad)
        by = 29.0 * math.sin(rad)
        ops.append(
            CircleExtrude(
                diameter_mm=3.2,
                x_mm=bx,
                y_mm=by,
                z_mm=-0.5,
                length_mm=pulley_w + 1.0,
                operation="cut",
            )
        )
    return FeaturePlan(name="rotor_gt2_pulley", operations=ops)


# --- 5. Stepper Motor Bracket ---

def plan_stepper_motor_bracket() -> FeaturePlan:
    """NEMA14 / NEMA17 Stepper Motor Bracket with 18mm belt-tension adjustment slots."""
    ops = [
        # Base Plate (Attaches to Housing)
        RectangleExtrude(
            width_mm=42.0,
            height_mm=38.0,
            x_mm=0.0,
            y_mm=19.0,
            z_mm=0.0,
            length_mm=5.0,
            operation="join",
        ),
        # Motor Face Plate (Perpendicular at 90 deg)
        RectangleExtrude(
            width_mm=42.0,
            height_mm=42.0,
            x_mm=0.0,
            y_mm=38.0,
            z_mm=0.0,
            length_mm=42.0,
            plane="XZ",
            operation="join",
        ),
        # NEMA Motor Center Bore (22mm)
        CircleExtrude(
            diameter_mm=22.0,
            x_mm=0.0,
            y_mm=38.0,
            z_mm=21.0,
            length_mm=6.0,
            plane="XZ",
            operation="cut",
        ),
        # 4x NEMA Motor M3 Mounting Holes (31x31mm spacing)
        CircleExtrude(diameter_mm=3.4, x_mm=-15.5, y_mm=38.0, z_mm=5.5, length_mm=6.0, plane="XZ", operation="cut"),
        CircleExtrude(diameter_mm=3.4, x_mm=15.5, y_mm=38.0, z_mm=5.5, length_mm=6.0, plane="XZ", operation="cut"),
        CircleExtrude(diameter_mm=3.4, x_mm=-15.5, y_mm=38.0, z_mm=36.5, length_mm=6.0, plane="XZ", operation="cut"),
        CircleExtrude(diameter_mm=3.4, x_mm=15.5, y_mm=38.0, z_mm=36.5, length_mm=6.0, plane="XZ", operation="cut"),
        # 2x Belt Tension Adjustment Slots on Base Plate (4.5mm wide, 18mm travel)
        RectangleExtrude(
            width_mm=4.5,
            height_mm=18.0,
            x_mm=-12.0,
            y_mm=15.0,
            z_mm=-0.5,
            length_mm=6.0,
            operation="cut",
        ),
        RectangleExtrude(
            width_mm=4.5,
            height_mm=18.0,
            x_mm=12.0,
            y_mm=15.0,
            z_mm=-0.5,
            length_mm=6.0,
            operation="cut",
        ),
    ]
    return FeaturePlan(name="stepper_motor_bracket", operations=ops)


# --- 6. Calibration Fit Coupons ---

def plan_bearing_fit_coupon() -> FeaturePlan:
    """Bearing fit coupon with 5 test bores: 65.00, 65.10, 65.20, 65.30, 65.40mm."""
    ops = [
        RectangleExtrude(width_mm=360.0, height_mm=75.0, x_mm=0.0, y_mm=0.0, z_mm=0.0, length_mm=8.0, operation="join"),
    ]
    bores = [65.00, 65.10, 65.20, 65.30, 65.40]
    for idx, bore in enumerate(bores):
        x = -140.0 + idx * 70.0
        ops.append(CircleExtrude(diameter_mm=bore, x_mm=x, y_mm=0.0, z_mm=-0.5, length_mm=9.0, operation="cut"))
    return FeaturePlan(name="bearing_fit_coupon", operations=ops)


def plan_rotor_fit_coupon() -> FeaturePlan:
    """Rotor fit coupon with 4 test pins: 49.70, 49.80, 49.90, 50.00mm."""
    ops = [
        RectangleExtrude(width_mm=240.0, height_mm=60.0, x_mm=0.0, y_mm=0.0, z_mm=0.0, length_mm=5.0, operation="join"),
    ]
    pins = [49.70, 49.80, 49.90, 50.00]
    for idx, pin in enumerate(pins):
        x = -90.0 + idx * 60.0
        ops.append(CircleExtrude(diameter_mm=pin, x_mm=x, y_mm=0.0, z_mm=5.0, length_mm=10.0, operation="join"))
    return FeaturePlan(name="rotor_fit_coupon", operations=ops)


def plan_adapter_fit_coupon() -> FeaturePlan:
    """Adapter clamp fit coupon with test bores: 54.00, 54.20, 54.40mm."""
    ops = [
        RectangleExtrude(width_mm=210.0, height_mm=65.0, x_mm=0.0, y_mm=0.0, z_mm=0.0, length_mm=8.0, operation="join"),
    ]
    bores = [54.00, 54.20, 54.40]
    for idx, bore in enumerate(bores):
        x = -70.0 + idx * 70.0
        ops.append(CircleExtrude(diameter_mm=bore, x_mm=x, y_mm=0.0, z_mm=-0.5, length_mm=9.0, operation="cut"))
    return FeaturePlan(name="adapter_fit_coupon", operations=ops)


def main():
    print("Connecting to Autodesk Inventor COM API...", flush=True)
    app = connect(visible=True)
    print("Connected to Autodesk Inventor successfully!", flush=True)

    # 1. Build and export all modular IPT and STL parts
    plans = [
        (plan_bearing_housing_upper(), GENERATED_DIR / "bearing_housing_upper.ipt", GENERATED_DIR / "bearing_housing_upper.stl"),
        (plan_bearing_housing_lower(), GENERATED_DIR / "bearing_housing_lower.ipt", GENERATED_DIR / "bearing_housing_lower.stl"),
        (plan_rotor_spindle(), GENERATED_DIR / "rotor_spindle.ipt", GENERATED_DIR / "rotor_spindle.stl"),
        (plan_camera_adapter_clamp(), GENERATED_DIR / "camera_adapter_clamp.ipt", GENERATED_DIR / "camera_adapter_clamp.stl"),
        (plan_telescope_adapter_clamp(), GENERATED_DIR / "telescope_adapter_clamp.ipt", GENERATED_DIR / "telescope_adapter_clamp.stl"),
        (plan_rotor_gt2_pulley(), GENERATED_DIR / "rotor_gt2_pulley.ipt", GENERATED_DIR / "rotor_gt2_pulley.stl"),
        (plan_stepper_motor_bracket(), GENERATED_DIR / "stepper_motor_bracket.ipt", GENERATED_DIR / "stepper_motor_bracket.stl"),
        (plan_bearing_fit_coupon(), GENERATED_DIR / "bearing_fit_coupon.ipt", GENERATED_DIR / "bearing_fit_coupon.stl"),
        (plan_rotor_fit_coupon(), GENERATED_DIR / "rotor_fit_coupon.ipt", GENERATED_DIR / "rotor_fit_coupon.stl"),
        (plan_adapter_fit_coupon(), GENERATED_DIR / "adapter_fit_coupon.ipt", GENERATED_DIR / "adapter_fit_coupon.stl"),
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
    iam_path = GENERATED_DIR / "camera_rotator_assembly.iam"
    print(f"\nBuilding True Inventor Assembly: {iam_path.name}...", flush=True)

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

    # Add Lower Housing (Grounded at origin)
    m_lower = tg.CreateMatrix()
    comp_def.Occurrences.Add(str(saved_parts["bearing_housing_lower"].resolve()), m_lower)
    print("  + Added Lower Bearing Housing", flush=True)

    # Add Upper Housing (Mated on top)
    m_upper = tg.CreateMatrix()
    comp_def.Occurrences.Add(str(saved_parts["bearing_housing_upper"].resolve()), m_upper)
    print("  + Added Upper Bearing Housing", flush=True)

    # Add Rotor Spindle (Concentric along optical Z axis)
    m_rotor = tg.CreateMatrix()
    m_rotor.SetTranslation(tg.CreateVector(0, 0, mm_to_cm(-6.0)))
    comp_def.Occurrences.Add(str(saved_parts["rotor_spindle"].resolve()), m_rotor)
    print("  + Added Rotor Spindle", flush=True)

    # Add GT2 Pulley (Bolted to rotor flange)
    m_pulley = tg.CreateMatrix()
    m_pulley.SetTranslation(tg.CreateVector(0, 0, mm_to_cm(26.0)))
    comp_def.Occurrences.Add(str(saved_parts["rotor_gt2_pulley"].resolve()), m_pulley)
    print("  + Added 120T GT2 Pulley", flush=True)

    # Add Camera Adapter Clamp
    m_cam_clamp = tg.CreateMatrix()
    m_cam_clamp.SetTranslation(tg.CreateVector(0, 0, mm_to_cm(36.0)))
    comp_def.Occurrences.Add(str(saved_parts["camera_adapter_clamp"].resolve()), m_cam_clamp)
    print("  + Added Camera Adapter Clamp", flush=True)

    # Add Telescope Adapter Clamp
    m_tel_clamp = tg.CreateMatrix()
    m_tel_clamp.SetTranslation(tg.CreateVector(0, 0, mm_to_cm(-12.0)))
    comp_def.Occurrences.Add(str(saved_parts["telescope_adapter_clamp"].resolve()), m_tel_clamp)
    print("  + Added Telescope Adapter Clamp", flush=True)

    # Add Stepper Motor Bracket
    m_motor_bracket = tg.CreateMatrix()
    m_motor_bracket.SetTranslation(tg.CreateVector(0, mm_to_cm(-45.0), mm_to_cm(5.0)))
    comp_def.Occurrences.Add(str(saved_parts["stepper_motor_bracket"].resolve()), m_motor_bracket)
    print("  + Added Stepper Motor Bracket", flush=True)

    asm_doc.SaveAs(str(iam_path.resolve()), False)
    print(f"\n[OK] Successfully built and saved True Inventor Assembly: {iam_path.name} ({iam_path.stat().st_size} bytes)", flush=True)
    print("[OK] All Camera Rotator CAD parts (.IPT, .STL) and assembly (.IAM) completed!", flush=True)


if __name__ == "__main__":
    main()
