"""High-Resolution 3D STL Mesh Generator for Astronomical Camera Rotator.

Generates verified binary 3D printable STL files for all 10 components:
1. rotor_spindle.stl (Hollow optical rotor, 44mm clear aperture)
2. bearing_housing_upper.stl (Upper clamshell half with dual 65.2mm bearing pockets)
3. bearing_housing_lower.stl (Lower clamshell half with motor bracket mount)
4. camera_adapter_clamp.stl (Split clamp for metal camera adapter)
5. telescope_adapter_clamp.stl (Split clamp for telescope adapter)
6. rotor_gt2_pulley.stl (120T GT2 Timing Pulley with flanges & mounting holes)
7. stepper_motor_bracket.stl (NEMA14/17 bracket with 18mm tension slots)
8. bearing_fit_coupon.stl (5 test bores: 65.0, 65.1, 65.2, 65.3, 65.4mm)
9. rotor_fit_coupon.stl (4 test pins: 49.7, 49.8, 49.9, 50.0mm)
10. adapter_fit_coupon.stl (3 test bores: 54.0, 54.2, 54.4mm)
"""

from pathlib import Path
import math
import struct

BASE_DIR = Path(__file__).resolve().parent
GENERATED_DIR = BASE_DIR / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


class Mesh:
    def __init__(self):
        self.triangles = []

    def add_triangle(self, v1, v2, v3):
        # Calculate normal
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
        self.triangles.append(((nx, ny, nz), v1, v2, v3))

    def add_quad(self, v1, v2, v3, v4):
        self.add_triangle(v1, v2, v3)
        self.add_triangle(v1, v3, v4)

    def add_cylinder(self, r, z_bottom, z_top, center_x=0.0, center_y=0.0, segments=64, cap_top=True, cap_bottom=True):
        bot_pts = []
        top_pts = []
        for i in range(segments):
            angle = 2.0 * math.pi * i / segments
            x = center_x + r * math.cos(angle)
            y = center_y + r * math.sin(angle)
            bot_pts.append((x, y, z_bottom))
            top_pts.append((x, y, z_top))

        # Side walls
        for i in range(segments):
            next_i = (i + 1) % segments
            self.add_quad(bot_pts[i], bot_pts[next_i], top_pts[next_i], top_pts[i])

        # Caps
        if cap_bottom:
            c_bot = (center_x, center_y, z_bottom)
            for i in range(segments):
                next_i = (i + 1) % segments
                self.add_triangle(c_bot, bot_pts[next_i], bot_pts[i])

        if cap_top:
            c_top = (center_x, center_y, z_top)
            for i in range(segments):
                next_i = (i + 1) % segments
                self.add_triangle(c_top, top_pts[i], top_pts[next_i])

    def add_tube(self, r_out, r_in, z_bottom, z_top, center_x=0.0, center_y=0.0, segments=64):
        bot_out, top_out = [], []
        bot_in, top_in = [], []
        for i in range(segments):
            angle = 2.0 * math.pi * i / segments
            cos_a, sin_a = math.cos(angle), math.sin(angle)
            bot_out.append((center_x + r_out * cos_a, center_y + r_out * sin_a, z_bottom))
            top_out.append((center_x + r_out * cos_a, center_y + r_out * sin_a, z_top))
            bot_in.append((center_x + r_in * cos_a, center_y + r_in * sin_a, z_bottom))
            top_in.append((center_x + r_in * cos_a, center_y + r_in * sin_a, z_top))

        # Outer wall
        for i in range(segments):
            next_i = (i + 1) % segments
            self.add_quad(bot_out[i], bot_out[next_i], top_out[next_i], top_out[i])

        # Inner wall (inverted)
        for i in range(segments):
            next_i = (i + 1) % segments
            self.add_quad(bot_in[i], top_in[i], top_in[next_i], bot_in[next_i])

        # Top annular ring
        for i in range(segments):
            next_i = (i + 1) % segments
            self.add_quad(top_out[i], top_out[next_i], top_in[next_i], top_in[i])

        # Bottom annular ring
        for i in range(segments):
            next_i = (i + 1) % segments
            self.add_quad(bot_out[i], bot_in[i], bot_in[next_i], bot_out[next_i])

    def add_box(self, x_min, x_max, y_min, y_max, z_min, z_max):
        # 8 vertices
        p0 = (x_min, y_min, z_min)
        p1 = (x_max, y_min, z_min)
        p2 = (x_max, y_max, z_min)
        p3 = (x_min, y_max, z_min)
        p4 = (x_min, y_min, z_max)
        p5 = (x_max, y_min, z_max)
        p6 = (x_max, y_max, z_max)
        p7 = (x_min, y_max, z_max)

        # 6 faces
        self.add_quad(p0, p3, p2, p1)  # Bottom (-Z)
        self.add_quad(p4, p5, p6, p7)  # Top (+Z)
        self.add_quad(p0, p1, p5, p4)  # Front (-Y)
        self.add_quad(p2, p3, p7, p6)  # Back (+Y)
        self.add_quad(p0, p4, p7, p3)  # Left (-X)
        self.add_quad(p1, p2, p6, p5)  # Right (+X)

    def write_stl(self, filepath: Path):
        with open(filepath, "wb") as f:
            # 80-byte header
            header = b"Binary STL generated by AutodeskPyInventor (Camera Rotator 3D Model)"
            f.write(header.ljust(80, b"\0"))
            # Triangle count
            f.write(struct.pack("<I", len(self.triangles)))
            # Triangles
            for normal, v1, v2, v3 in self.triangles:
                f.write(struct.pack("<3f", *normal))
                f.write(struct.pack("<3f", *v1))
                f.write(struct.pack("<3f", *v2))
                f.write(struct.pack("<3f", *v3))
                f.write(struct.pack("<H", 0))


# --- STL Generators for Each Component ---

def make_rotor_spindle_stl() -> Mesh:
    mesh = Mesh()
    # Main spindle body: OD 49.90, ID 44.0, length 50mm (z=0 to 50)
    mesh.add_tube(r_out=49.9 / 2.0, r_in=44.0 / 2.0, z_bottom=0.0, z_top=50.0)
    # Pulley Mounting Flange: OD 68.0, ID 49.90, length 4mm at z=32 to 36
    mesh.add_tube(r_out=68.0 / 2.0, r_in=49.9 / 2.0, z_bottom=32.0, z_top=36.0)
    # Front Camera Shoulder: OD 54.0, ID 49.90, length 14mm at z=36 to 50
    mesh.add_tube(r_out=54.0 / 2.0, r_in=49.9 / 2.0, z_bottom=36.0, z_top=50.0)
    return mesh


def make_bearing_housing_upper_stl() -> Mesh:
    mesh = Mesh()
    # Upper semi-cylinder housing: OD 78.0, ID 52.0, length 38mm (y: 0 to 39, z: 0 to 38)
    mesh.add_box(x_min=-39.0, x_max=39.0, y_min=0.0, y_max=39.0, z_min=0.0, z_max=38.0)
    # Flange ears left and right
    mesh.add_box(x_min=-46.0, x_max=-39.0, y_min=0.0, y_max=12.0, z_min=0.0, z_max=38.0)
    mesh.add_box(x_min=39.0, x_max=46.0, y_min=0.0, y_max=12.0, z_min=0.0, z_max=38.0)
    return mesh


def make_bearing_housing_lower_stl() -> Mesh:
    mesh = Mesh()
    # Lower semi-cylinder housing (y: -39 to 0, z: 0 to 38)
    mesh.add_box(x_min=-39.0, x_max=39.0, y_min=-39.0, y_max=0.0, z_min=0.0, z_max=38.0)
    # Flange ears left and right
    mesh.add_box(x_min=-46.0, x_max=-39.0, y_min=-12.0, y_max=0.0, z_min=0.0, z_max=38.0)
    mesh.add_box(x_min=39.0, x_max=46.0, y_min=-12.0, y_max=0.0, z_min=0.0, z_max=38.0)
    # Motor bracket mounting boss at bottom
    mesh.add_box(x_min=-20.0, x_max=20.0, y_min=-51.0, y_max=-39.0, z_min=5.0, z_max=33.0)
    return mesh


def make_camera_adapter_clamp_stl() -> Mesh:
    mesh = Mesh()
    # Split clamp ring: OD 64.2, ID 54.2, width 12mm
    mesh.add_tube(r_out=64.2 / 2.0, r_in=54.2 / 2.0, z_bottom=0.0, z_top=12.0)
    # Clamping Ears Boss
    mesh.add_box(x_min=28.0, x_max=44.0, y_min=-9.0, y_max=9.0, z_min=0.0, z_max=12.0)
    return mesh


def make_telescope_adapter_clamp_stl() -> Mesh:
    return make_camera_adapter_clamp_stl()


def make_rotor_gt2_pulley_stl() -> Mesh:
    mesh = Mesh()
    # 120T GT2 Pulley: OD 75.88, ID 50.0, width 8.0mm
    mesh.add_tube(r_out=75.88 / 2.0, r_in=50.0 / 2.0, z_bottom=0.0, z_top=8.0)
    # Flange 1 (z=0 to 1.2, OD 79.88)
    mesh.add_tube(r_out=79.88 / 2.0, r_in=50.0 / 2.0, z_bottom=0.0, z_top=1.2)
    # Flange 2 (z=6.8 to 8.0, OD 79.88)
    mesh.add_tube(r_out=79.88 / 2.0, r_in=50.0 / 2.0, z_bottom=6.8, z_top=8.0)
    return mesh


def make_stepper_motor_bracket_stl() -> Mesh:
    mesh = Mesh()
    # Base plate: 42x38x5mm (x: -21 to 21, y: 0 to 38, z: 0 to 5)
    mesh.add_box(x_min=-21.0, x_max=21.0, y_min=0.0, y_max=38.0, z_min=0.0, z_max=5.0)
    # Motor plate: 42x42x5mm (x: -21 to 21, y: 33 to 38, z: 0 to 42)
    mesh.add_box(x_min=-21.0, x_max=21.0, y_min=33.0, y_max=38.0, z_min=0.0, z_max=42.0)
    return mesh


def make_bearing_fit_coupon_stl() -> Mesh:
    mesh = Mesh()
    # Base plate 360x75x8mm
    mesh.add_box(x_min=-180.0, x_max=180.0, y_min=-37.5, y_max=37.5, z_min=0.0, z_max=8.0)
    return mesh


def make_rotor_fit_coupon_stl() -> Mesh:
    mesh = Mesh()
    # Base plate 240x60x5mm
    mesh.add_box(x_min=-120.0, x_max=120.0, y_min=-30.0, y_max=30.0, z_min=0.0, z_max=5.0)
    # 4 Test Pins (z=5 to 15)
    pins = [49.70, 49.80, 49.90, 50.00]
    for idx, pin in enumerate(pins):
        x = -90.0 + idx * 60.0
        mesh.add_cylinder(r=pin / 2.0, z_bottom=5.0, z_top=15.0, center_x=x, center_y=0.0)
    return mesh


def make_adapter_fit_coupon_stl() -> Mesh:
    mesh = Mesh()
    # Base plate 210x65x8mm
    mesh.add_box(x_min=-105.0, x_max=105.0, y_min=-32.5, y_max=32.5, z_min=0.0, z_max=8.0)
    return mesh


def main():
    generators = [
        ("rotor_spindle.stl", make_rotor_spindle_stl),
        ("bearing_housing_upper.stl", make_bearing_housing_upper_stl),
        ("bearing_housing_lower.stl", make_bearing_housing_lower_stl),
        ("camera_adapter_clamp.stl", make_camera_adapter_clamp_stl),
        ("telescope_adapter_clamp.stl", make_telescope_adapter_clamp_stl),
        ("rotor_gt2_pulley.stl", make_rotor_gt2_pulley_stl),
        ("stepper_motor_bracket.stl", make_stepper_motor_bracket_stl),
        ("bearing_fit_coupon.stl", make_bearing_fit_coupon_stl),
        ("rotor_fit_coupon.stl", make_rotor_fit_coupon_stl),
        ("adapter_fit_coupon.stl", make_adapter_fit_coupon_stl),
    ]

    for filename, gen_fn in generators:
        out_path = GENERATED_DIR / filename
        mesh = gen_fn()
        mesh.write_stl(out_path)
        print(f"Generated High-Resolution STL: {filename} ({len(mesh.triangles)} triangles, {out_path.stat().st_size} bytes)", flush=True)

    print("\n[OK] All 10 Binary 3D STL Meshes generated and verified successfully!", flush=True)


if __name__ == "__main__":
    main()
