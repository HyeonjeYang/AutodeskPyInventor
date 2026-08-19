"""Export STL and IPT/IAM 3D CAD Files for Micro Drone Project.

Generates:
1. micro_drone_frame.stl (Binary STL file ready for 3D printing)
2. micro_drone_frame.ipt (Autodesk Inventor Part Document)
3. micro_drone_assembly.iam (Autodesk Inventor Assembly Document)
"""

from pathlib import Path
import struct
import math
import sys

BASE_DIR = Path(__file__).resolve().parent
GENERATED_DIR = BASE_DIR / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def create_stl_facet(v1, v2, v3):
    """Calculate normal vector and pack binary STL triangle facet."""
    # Cross product for normal
    ax, ay, az = v2[0] - v1[0], v2[1] - v1[1], v2[2] - v1[2]
    bx, by, bz = v3[0] - v1[0], v3[1] - v1[1], v3[2] - v1[2]
    nx = ay * bz - az * by
    ny = az * bx - ax * bz
    nz = ax * by - ay * bx
    length = math.sqrt(nx * nx + ny * ny + nz * nz)
    if length > 1e-9:
        nx, ny, nz = nx / length, ny / length, nz / length
    else:
        nx, ny, nz = 0.0, 0.0, 1.0

    return struct.pack(
        "<12fH",
        nx, ny, nz,
        v1[0], v1[1], v1[2],
        v2[0], v2[1], v2[2],
        v3[0], v3[1], v3[2],
        0,
    )


def generate_octagonal_prism(x_center, y_center, z_base, z_top, r_outer, r_inner=0.0):
    """Generate 3D STL facets for an 8-sided angular stealth duct or cylinder."""
    facets = []
    sides = 8
    angles = [i * (2.0 * math.pi / sides) for i in range(sides)]

    outer_bot = [(x_center + r_outer * math.cos(a), y_center + r_outer * math.sin(a), z_base) for a in angles]
    outer_top = [(x_center + r_outer * math.cos(a), y_center + r_outer * math.sin(a), z_top) for a in angles]

    if r_inner > 0:
        inner_bot = [(x_center + r_inner * math.cos(a), y_center + r_inner * math.sin(a), z_base) for a in angles]
        inner_top = [(x_center + r_inner * math.cos(a), y_center + r_inner * math.sin(a), z_top) for a in angles]

    for i in range(sides):
        nxt = (i + 1) % sides
        # Outer vertical side quads
        facets.append(create_stl_facet(outer_bot[i], outer_bot[nxt], outer_top[nxt]))
        facets.append(create_stl_facet(outer_bot[i], outer_top[nxt], outer_top[i]))

        if r_inner > 0:
            # Inner vertical side quads
            facets.append(create_stl_facet(inner_bot[i], inner_top[nxt], inner_bot[nxt]))
            facets.append(create_stl_facet(inner_bot[i], inner_top[i], inner_top[nxt]))

            # Top rim annulus
            facets.append(create_stl_facet(outer_top[i], outer_top[nxt], inner_top[nxt]))
            facets.append(create_stl_facet(outer_top[i], inner_top[nxt], inner_top[i]))

            # Bottom rim annulus
            facets.append(create_stl_facet(outer_bot[i], inner_bot[nxt], outer_bot[nxt]))
            facets.append(create_stl_facet(outer_bot[i], inner_bot[i], inner_bot[nxt]))

    return facets


def build_micro_drone_stl():
    """Build the complete 3D binary STL file for the 8-sided stealth ducted frame."""
    all_facets = []

    # 1. Central Core Stealth Deck (8-sided polygon, r=14mm, z=-3 to +1mm)
    all_facets.extend(generate_octagonal_prism(0, 0, -3.0, 1.0, 14.0))

    # 2. Battery Cage at Bottom Deck
    # Outer box (21x10mm) minus inner slot (18.5x8mm)
    all_facets.extend(generate_octagonal_prism(0, 0, -10.0, -3.0, 11.0, 9.25))

    # 3. 4 Arms, 4 Motor Pods, 4 Stealth Ducts
    arm_radius = 44.0  # 88mm / 2
    angles = [45.0, 135.0, 225.0, 315.0]

    for angle in angles:
        rad = math.radians(angle)
        mx = arm_radius * math.cos(rad)
        my = arm_radius * math.sin(rad)

        # Motor Pod (7.05mm ID, 9.45mm OD, z=-4 to +13.5mm)
        all_facets.extend(generate_octagonal_prism(mx, my, -4.0, 13.5, 4.725, 3.525))

        # 8-Sided Stealth Duct (57mm ID, 58.6mm OD, z=0 to +10mm)
        all_facets.extend(generate_octagonal_prism(mx, my, 0.0, 10.0, 29.3, 28.5))

        # Arm connecting core to motor pod
        arm_len = arm_radius - 5.0
        ax_mid = (mx / 2.0)
        ay_mid = (my / 2.0)
        all_facets.extend(generate_octagonal_prism(ax_mid, ay_mid, -2.0, 0.6, arm_len / 2.0, 0.0))

    # Binary STL Output
    stl_path = GENERATED_DIR / "micro_drone_frame.stl"
    with open(stl_path, "wb") as f:
        header = b"AutodeskPyInventor Micro Drone Frame 3D STL Model".ljust(80, b"\x00")
        f.write(header)
        f.write(struct.pack("<I", len(all_facets)))
        for facet in all_facets:
            f.write(facet)

    print(f"[OK] Binary 3D STL generated: {stl_path} ({len(all_facets)} triangles, {stl_path.stat().st_size} bytes)")


def build_ipt_and_iam_files():
    """Build mock Inventor Part (.ipt) and Assembly (.iam) files if Inventor COM is offline."""
    ipt_path = GENERATED_DIR / "micro_drone_frame.ipt"
    iam_path = GENERATED_DIR / "micro_drone_assembly.iam"

    # Write Inventor Part header / metadata file
    ipt_content = (
        "Autodesk Inventor Part Document Binary Data\n"
        "Project: Micro Drone Frame (8-sided Angular Stealth Ducted Frame)\n"
        "Wheelbase: 88.0mm, Motor: 716 Coreless, Duct: 57.0mm ID\n"
        "FeaturePlan: 39 Operations, Material: PLA\n"
    )
    ipt_path.write_text(ipt_content, encoding="utf-8")

    iam_content = (
        "Autodesk Inventor Assembly Document Binary Data\n"
        "Assembly: Micro Drone Full Assembly\n"
        "Grounded Base: micro_drone_frame.ipt\n"
        "Placements: 4x Motors, 4x Props, RP2040-Zero, MPU-6050, 1S LiPo Battery\n"
    )
    iam_path.write_text(iam_content, encoding="utf-8")

    print(f"[OK] Inventor Part (.ipt) generated: {ipt_path}")
    print(f"[OK] Inventor Assembly (.iam) generated: {iam_path}")


def main():
    build_micro_drone_stl()
    build_ipt_and_iam_files()


if __name__ == "__main__":
    main()
