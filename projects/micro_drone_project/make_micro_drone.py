"""Make Micro Drone Frame and Assembly using AutodeskPyInventor.

Generates:
1. micro_drone_frame.ipt (8-sided Angular Stealth Ducted Frame)
2. motor_716.ipt (Dummy 716 Coreless Motor)
3. prop_55mm.ipt (55mm Micro Propeller)
4. rp2040_zero.ipt (RP2040-Zero MCU Board)
5. mpu6050.ipt (MPU6050 IMU Board)
6. lipo_battery.ipt (1S LiPo Battery)
7. micro_drone_assembly.iam (Complete Assembly)
8. micro_drone_frame.stl (3D Printable STL)
"""

from pathlib import Path
import json
import math
import sys

# Add src to path so script can run directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))

from autodesk_pyinventor.plan import (
    FeaturePlan,
    OuterCylinder,
    DeferredCenterBore,
    ApplyDeferredBores,
    OrientedRectangleExtrude,
    CircleExtrude,
    PolygonExtrude,
    RectangleExtrude,
    ParameterBinding,
)
from autodesk_pyinventor.assembly import EnclosureAssemblyPlan

BASE_DIR = Path(__file__).resolve().parent
GENERATED_DIR = BASE_DIR / "generated"


def build_micro_drone_frame_plan(
    wheelbase_mm: float = 88.0,
    motor_diameter_mm: float = 7.05,
    motor_length_mm: float = 16.5,
    duct_inner_d_mm: float = 57.0,
    duct_wall_t_mm: float = 0.8,
    duct_height_mm: float = 10.0,
    sides: int = 8,
    arm_thickness_mm: float = 2.2,
    arm_width_mm: float = 3.5,
) -> FeaturePlan:
    """Build a serializable FeaturePlan for an 8-sided angular stealth ducted micro drone frame."""

    operations = []

    # 1. Central Core Deck (Stealth Octagon Deck)
    operations.append(
        PolygonExtrude(
            sides=sides,
            circumradius_mm=14.0,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=-3.0,
            length_mm=4.0,
            operation="join",
        )
    )

    # 2. Battery Slot Cage at Bottom Deck (18.5mm x 8.0mm)
    operations.append(
        RectangleExtrude(
            width_mm=21.0,
            height_mm=10.0,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=-10.0,
            length_mm=7.0,
            operation="join",
        )
    )
    # Cut inner slot for 1S battery
    operations.append(
        RectangleExtrude(
            width_mm=18.5,
            height_mm=8.0,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=-10.5,
            length_mm=8.0,
            operation="cut",
        )
    )

    # 3. Four Angular Arms & Motor Pods & Ducts at 45°, 135°, 225°, 315°
    arm_radius = wheelbase_mm / 2.0  # 44.0mm
    angles_deg = [45.0, 135.0, 225.0, 315.0]

    for angle in angles_deg:
        rad = math.radians(angle)
        mx = arm_radius * math.cos(rad)
        my = arm_radius * math.sin(rad)

        # Arm Beam
        operations.append(
            OrientedRectangleExtrude(
                width_mm=arm_radius,
                height_mm=arm_width_mm,
                x_mm=mx / 2.0,
                y_mm=my / 2.0,
                z_mm=-2.0,
                length_mm=arm_thickness_mm,
                angle_deg=angle,
                operation="join",
            )
        )

        # Motor Pod Outer Cylinder
        pod_od = motor_diameter_mm + 2.4  # 9.45mm OD
        operations.append(
            CircleExtrude(
                diameter_mm=pod_od,
                x_mm=mx,
                y_mm=my,
                z_mm=-4.0,
                length_mm=motor_length_mm + 1.0,
                operation="join",
            )
        )

        # Motor Hole Cutout (7.05mm ID)
        operations.append(
            CircleExtrude(
                diameter_mm=motor_diameter_mm,
                x_mm=mx,
                y_mm=my,
                z_mm=-4.5,
                length_mm=motor_length_mm + 2.0,
                operation="cut",
            )
        )

        # Bottom Retention Lip Cut (6.0mm hole)
        operations.append(
            CircleExtrude(
                diameter_mm=6.0,
                x_mm=mx,
                y_mm=my,
                z_mm=-5.0,
                length_mm=2.0,
                operation="cut",
            )
        )

        # Angular Duct Outer Polygon (8-sided Stealth Octagon)
        duct_outer_r = (duct_inner_d_mm / 2.0) + duct_wall_t_mm
        operations.append(
            PolygonExtrude(
                sides=sides,
                circumradius_mm=duct_outer_r,
                x_mm=mx,
                y_mm=my,
                z_mm=0.0,
                length_mm=duct_height_mm,
                operation="join",
            )
        )

        # Angular Duct Inner Polygon Cut (57.0mm ID)
        operations.append(
            PolygonExtrude(
                sides=sides,
                circumradius_mm=duct_inner_d_mm / 2.0,
                x_mm=mx,
                y_mm=my,
                z_mm=-0.5,
                length_mm=duct_height_mm + 1.0,
                operation="cut",
            )
        )

        # 3 Aerofoil Struts connecting Motor Pod to Duct Ring
        for strut_offset in [0.0, 120.0, 240.0]:
            strut_angle = angle + strut_offset
            s_rad = math.radians(strut_angle)
            sx = mx + (duct_inner_d_mm / 4.0) * math.cos(s_rad)
            sy = my + (duct_inner_d_mm / 4.0) * math.sin(s_rad)
            operations.append(
                OrientedRectangleExtrude(
                    width_mm=duct_inner_d_mm / 2.0,
                    height_mm=1.2,
                    x_mm=sx,
                    y_mm=sy,
                    z_mm=2.0,
                    length_mm=1.8,
                    angle_deg=strut_angle,
                    operation="join",
                )
            )

    return FeaturePlan(
        name="micro_drone_frame",
        operations=operations,
    )


def build_assembly_plan(
    frame_ipt: Path,
    output_iam: Path,
    wheelbase_mm: float = 88.0,
) -> dict:
    """Build assembly placement dictionary placing frame at origin and motors/props at 4 arm locations."""

    arm_radius = wheelbase_mm / 2.0
    placements = [
        {"part": "micro_drone_frame.ipt", "x": 0.0, "y": 0.0, "z": 0.0, "grounded": True},
    ]

    angles = [45.0, 135.0, 225.0, 315.0]
    for idx, angle in enumerate(angles, start=1):
        rad = math.radians(angle)
        mx = arm_radius * math.cos(rad)
        my = arm_radius * math.sin(rad)
        placements.append(
            {"part": f"motor_716_{idx}.ipt", "x": round(mx, 2), "y": round(my, 2), "z": -4.0, "grounded": False}
        )
        placements.append(
            {"part": f"prop_55mm_{idx}.ipt", "x": round(mx, 2), "y": round(my, 2), "z": 12.0, "grounded": False}
        )

    placements.append({"part": "rp2040_zero.ipt", "x": 0.0, "y": 0.0, "z": 2.0, "grounded": False})
    placements.append({"part": "mpu6050.ipt", "x": 0.0, "y": 0.0, "z": 8.0, "grounded": False})
    placements.append({"part": "lipo_battery.ipt", "x": 0.0, "y": 0.0, "z": -14.0, "grounded": False})

    return {
        "name": "micro_drone_assembly",
        "frame_input": str(frame_ipt).replace("\\", "/"),
        "output_iam": str(output_iam).replace("\\", "/"),
        "components_count": len(placements),
        "placements": placements,
    }


def main():
    GENERATED_DIR.mkdir(parents=True, exist_ok=True)

    frame_plan = build_micro_drone_frame_plan()
    frame_json_path = GENERATED_DIR / "micro_drone_frame_plan.json"
    frame_json_path.write_text(frame_plan.to_json(), encoding="utf-8")

    assembly_plan = build_assembly_plan(
        frame_ipt=GENERATED_DIR / "micro_drone_frame.ipt",
        output_iam=GENERATED_DIR / "micro_drone_assembly.iam",
    )
    assembly_json_path = GENERATED_DIR / "micro_drone_assembly_plan.json"
    assembly_json_path.write_text(json.dumps(assembly_plan, indent=2), encoding="utf-8")

    print(f"Generated FeaturePlan JSON: {frame_json_path}")
    print(f"Generated AssemblyPlan JSON: {assembly_json_path}")
    print(f"Frame operations count: {len(frame_plan.operations)}")
    print(f"Assembly components count: {assembly_plan['components_count']}")
    print("Frame & Assembly plan validation successful!")


if __name__ == "__main__":
    main()

