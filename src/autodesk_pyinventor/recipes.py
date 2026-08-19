"""Manufacturing-oriented geometry recipes."""

from __future__ import annotations

from numbers import Real

from .exceptions import InventorValidationError
from .plan import (
    ApplyDeferredBores,
    AnnularSectorExtrude,
    CircleExtrude,
    DeferredCenterBore,
    EnclosurePlan,
    ExtentDirection,
    FeaturePlan,
    MultiPartPlan,
    Operation,
    OuterCylinder,
    OrientedRectangleExtrude,
    ParameterBinding,
    PolygonExtrude,
    ProfileExtrude,
    RectangleExtrude,
    Shell,
)
from .validation import (
    ensure_at_least,
    ensure_outer_greater_than_inner,
    non_negative_mm,
    numeric_mm,
    positive_mm,
)


def disk_plan(
    *,
    name: str = "disk",
    od: Real,
    id: Real = 0,
    thickness: Real = 1,
) -> FeaturePlan:
    """Plan a disk or washer as one outer solid plus one optional final bore."""

    outer_diameter = positive_mm("od", od)
    inner_diameter = non_negative_mm("id", id)
    depth = positive_mm("thickness", thickness)
    if inner_diameter > 0:
        ensure_outer_greater_than_inner("od", outer_diameter, "id", inner_diameter)

    operations = [OuterCylinder(diameter_mm=outer_diameter, z_mm=0, length_mm=depth)]
    if inner_diameter > 0:
        operations.extend(
            [
                DeferredCenterBore(diameter_mm=inner_diameter),
                ApplyDeferredBores(),
            ]
        )
    return FeaturePlan(name=name, operations=operations)


def washer_plan(*, name: str = "washer", od: Real, id: Real, thickness: Real) -> FeaturePlan:
    """Plan a washer as a disk with a required center bore."""

    return disk_plan(name=name, od=od, id=id, thickness=thickness)


def tube_plan(*, name: str = "tube", od: Real, id: Real, length: Real) -> FeaturePlan:
    """Plan a straight tube with the through bore applied once at the end."""

    outer_diameter = positive_mm("od", od)
    inner_diameter = non_negative_mm("id", id)
    tube_length = positive_mm("length", length)
    if inner_diameter > 0:
        ensure_outer_greater_than_inner("od", outer_diameter, "id", inner_diameter)

    operations = [OuterCylinder(diameter_mm=outer_diameter, z_mm=0, length_mm=tube_length)]
    if inner_diameter > 0:
        operations.extend(
            [
                DeferredCenterBore(diameter_mm=inner_diameter),
                ApplyDeferredBores(),
            ]
        )
    return FeaturePlan(name=name, operations=operations)


def flanged_tube_plan(
    *,
    name: str = "flanged_tube",
    body_od: Real,
    body_id: Real,
    body_length: Real,
    flange_od: Real,
    flange_thickness: Real,
    flange_z: Real = 0,
) -> FeaturePlan:
    """Plan a flanged tube by joining all outer solids before one final bore."""

    body_outer = positive_mm("body_od", body_od)
    body_inner = non_negative_mm("body_id", body_id)
    length = positive_mm("body_length", body_length)
    flange_diameter = positive_mm("flange_od", flange_od)
    flange_depth = positive_mm("flange_thickness", flange_thickness)
    flange_position = numeric_mm("flange_z", flange_z)

    if body_inner > 0:
        ensure_outer_greater_than_inner("body_od", body_outer, "body_id", body_inner)
    ensure_at_least("flange_od", flange_diameter, "body_od", body_outer)

    operations = [
        OuterCylinder(diameter_mm=body_outer, z_mm=0, length_mm=length),
        OuterCylinder(
            diameter_mm=flange_diameter,
            z_mm=flange_position,
            length_mm=flange_depth,
        ),
    ]
    if body_inner > 0:
        operations.extend(
            [
                DeferredCenterBore(diameter_mm=body_inner),
                ApplyDeferredBores(),
            ]
        )
    return FeaturePlan(name=name, operations=operations)


def astro_controller_enclosure_plan(
    *,
    name: str = "astro_controller_enclosure",
    wall: Real = 2.0,
    out_x: Real = 84.0,
    out_y: Real = 58.0,
    base_h: Real = 29.5,
    lid_t: Real = 3.0,
    boss_h: Real = 4.0,
    fit: Real = 0.3,
    oled_window_width: Real = 23.0,
    oled_window_height: Real = 12.5,
    oled_window_x: Real = 28.0,
    oled_window_y: Real = 35.0,
    oled_pocket_size: Real = 28.6,
    oled_pocket_depth: Real = 1.8,
    encoder_hole_diameter: Real = 7.2,
) -> EnclosurePlan:
    """Build deterministic Base and Lid plans for the Astro Controller enclosure."""

    wall_mm = positive_mm("wall", wall)
    width_mm = positive_mm("out_x", out_x)
    depth_mm = positive_mm("out_y", out_y)
    base_height_mm = positive_mm("base_h", base_h)
    lid_thickness_mm = positive_mm("lid_t", lid_t)
    boss_height_mm = positive_mm("boss_h", boss_h)
    fit_mm = non_negative_mm("fit", fit)

    if width_mm <= wall_mm * 2 or depth_mm <= wall_mm * 2:
        raise InventorValidationError(
            "out_x and out_y must leave a positive inner cavity after wall thickness."
        )
    if base_height_mm <= wall_mm:
        raise InventorValidationError("base_h must be greater than wall.")
    if boss_height_mm > base_height_mm - wall_mm:
        raise InventorValidationError("boss_h must fit inside the Base height.")
    if width_mm > 200 or depth_mm > 200 or base_height_mm + lid_thickness_mm > 200:
        raise InventorValidationError(
            "The enclosure must fit within the 200 mm build-volume checklist limit."
        )

    oled_width_mm = positive_mm("oled_window_width", oled_window_width)
    oled_height_mm = positive_mm("oled_window_height", oled_window_height)
    oled_x_mm = numeric_mm("oled_window_x", oled_window_x)
    oled_y_mm = numeric_mm("oled_window_y", oled_window_y)
    pocket_size_mm = positive_mm("oled_pocket_size", oled_pocket_size)
    pocket_depth_mm = positive_mm("oled_pocket_depth", oled_pocket_depth)
    encoder_diameter_mm = positive_mm("encoder_hole_diameter", encoder_hole_diameter)

    _ensure_rectangle_inside(
        "OLED window",
        oled_x_mm,
        oled_y_mm,
        oled_width_mm,
        oled_height_mm,
        width_mm,
        depth_mm,
    )
    _ensure_rectangle_inside(
        "OLED pocket",
        oled_x_mm,
        oled_y_mm,
        pocket_size_mm,
        pocket_size_mm,
        width_mm,
        depth_mm,
    )
    if pocket_depth_mm >= lid_thickness_mm:
        raise InventorValidationError("oled_pocket_depth must be smaller than lid_t.")
    _ensure_point_inside("encoder hole", 62.0, 35.0, width_mm, depth_mm, encoder_diameter_mm / 2)

    pico_bosses = [(18.5, 34.3), (65.5, 34.3), (18.5, 45.7), (65.5, 45.7)]
    proto_bosses = [(34.5, 8.5), (49.5, 8.5), (34.5, 23.5), (49.5, 23.5)]
    corner_bosses = [(6.0, 6.0), (78.0, 6.0), (6.0, 50.0), (78.0, 50.0)]
    boss_groups = (
        ("Pico boss", pico_bosses, 2.25),
        ("Proto boss", proto_bosses, 2.25),
        ("corner boss", corner_bosses, 3.0),
    )
    all_bosses: list[tuple[str, float, float, float]] = []
    for label, centers, radius in boss_groups:
        for x_mm, y_mm in centers:
            _ensure_point_inside(label, x_mm, y_mm, width_mm, depth_mm, radius)
            all_bosses.append((label, x_mm, y_mm, radius))
    _ensure_circles_do_not_overlap(all_bosses)
    for x_mm, y_mm in corner_bosses:
        _ensure_point_inside("corner hole", x_mm, y_mm, width_mm, depth_mm, 3.0)

    base_operations: list[Operation] = [
        RectangleExtrude(
            width_mm=width_mm,
            height_mm=depth_mm,
            x_mm=width_mm / 2,
            y_mm=depth_mm / 2,
            z_mm=0,
            length_mm=base_height_mm,
        ),
        Shell(
            outer_width_mm=width_mm,
            outer_depth_mm=depth_mm,
            outer_height_mm=base_height_mm,
            thickness_mm=wall_mm,
        ),
    ]
    base_operations.extend(
        _circle_joins(pico_bosses, diameter=4.5, z=wall_mm, length=boss_height_mm)
    )
    base_operations.extend(
        _circle_cuts(
            pico_bosses,
            diameter=1.7,
            z=wall_mm + boss_height_mm,
            length=5.0,
            direction="negative",
        )
    )
    base_operations.extend(
        _circle_joins(proto_bosses, diameter=4.5, z=wall_mm, length=boss_height_mm)
    )
    base_operations.extend(
        _circle_cuts(
            proto_bosses,
            diameter=1.7,
            z=wall_mm + boss_height_mm,
            length=5.0,
            direction="negative",
        )
    )
    base_operations.extend(
        _circle_joins(corner_bosses, diameter=6.0, z=wall_mm, length=base_height_mm - wall_mm)
    )
    base_operations.extend(
        _circle_cuts(
            corner_bosses,
            diameter=2.5,
            z=base_height_mm,
            length=12.0,
            direction="negative",
        )
    )
    base_operations.extend(
        [
            RectangleExtrude(
                width_mm=13.0,
                height_mm=7.0,
                x_mm=width_mm,
                y_mm=40.0,
                z_mm=8.0,
                length_mm=wall_mm,
                operation="cut",
                plane="YZ",
                direction="negative",
            ),
            CircleExtrude(
                diameter_mm=5.2,
                x_mm=42.0,
                y_mm=0,
                z_mm=15.0,
                length_mm=wall_mm,
                operation="cut",
                plane="XZ",
                direction="positive",
            ),
            CircleExtrude(
                diameter_mm=6.0,
                x_mm=0,
                y_mm=40.0,
                z_mm=8.0,
                length_mm=wall_mm,
                operation="cut",
                plane="YZ",
                direction="positive",
            ),
        ]
    )

    lid_operations: list[Operation] = [
        RectangleExtrude(
            width_mm=width_mm,
            height_mm=depth_mm,
            x_mm=width_mm / 2,
            y_mm=depth_mm / 2,
            z_mm=0,
            length_mm=lid_thickness_mm,
        )
    ]
    for x_mm, y_mm in corner_bosses:
        lid_operations.extend(
            [
                CircleExtrude(
                    diameter_mm=3.2,
                    x_mm=x_mm,
                    y_mm=y_mm,
                    z_mm=lid_thickness_mm,
                    length_mm=lid_thickness_mm + 0.2,
                    operation="cut",
                    direction="negative",
                ),
                CircleExtrude(
                    diameter_mm=6.0,
                    x_mm=x_mm,
                    y_mm=y_mm,
                    z_mm=lid_thickness_mm,
                    length_mm=1.5,
                    operation="cut",
                    direction="negative",
                ),
            ]
        )
    lid_operations.extend(
        [
            RectangleExtrude(
                width_mm=oled_width_mm,
                height_mm=oled_height_mm,
                x_mm=oled_x_mm,
                y_mm=oled_y_mm,
                z_mm=lid_thickness_mm,
                length_mm=lid_thickness_mm + 0.2,
                operation="cut",
                direction="negative",
            ),
            RectangleExtrude(
                width_mm=pocket_size_mm,
                height_mm=pocket_size_mm,
                x_mm=oled_x_mm,
                y_mm=oled_y_mm,
                z_mm=0,
                length_mm=pocket_depth_mm,
                operation="cut",
            ),
            CircleExtrude(
                diameter_mm=encoder_diameter_mm,
                x_mm=62.0,
                y_mm=35.0,
                z_mm=lid_thickness_mm,
                length_mm=lid_thickness_mm + 0.2,
                operation="cut",
                direction="negative",
            ),
        ]
    )

    parameters = {
        "wall": wall_mm,
        "outX": width_mm,
        "outY": depth_mm,
        "baseH": base_height_mm,
        "lidT": lid_thickness_mm,
        "bossH": boss_height_mm,
        "fit": fit_mm,
        "oledWindowWidth": oled_width_mm,
        "oledWindowHeight": oled_height_mm,
        "oledWindowX": oled_x_mm,
        "oledWindowY": oled_y_mm,
        "oledPocketSize": pocket_size_mm,
        "oledPocketDepth": pocket_depth_mm,
        "encoderHoleDiameter": encoder_diameter_mm,
    }
    base_bindings = [
        ParameterBinding(0, "extent", "baseH"),
        ParameterBinding(1, "extent", "baseH - wall"),
        *[ParameterBinding(index, "extent", "bossH") for index in (*range(2, 6), *range(10, 14))],
        *[ParameterBinding(index, "extent", "baseH - wall") for index in range(18, 22)],
        *[ParameterBinding(index, "extent", "wall") for index in range(26, 29)],
    ]
    lid_bindings = [
        ParameterBinding(0, "extent", "lidT"),
        *[ParameterBinding(index, "extent", "lidT + 0.2 mm") for index in (1, 3, 5, 7)],
        ParameterBinding(9, "extent", "lidT + 0.2 mm"),
        ParameterBinding(10, "extent", "oledPocketDepth"),
        ParameterBinding(11, "extent", "lidT + 0.2 mm"),
    ]

    return EnclosurePlan(
        name=name,
        base=FeaturePlan(
            name=f"{name}_base",
            operations=base_operations,
            parameters=parameters,
            parameter_bindings=base_bindings,
        ),
        lid=FeaturePlan(
            name=f"{name}_lid",
            operations=lid_operations,
            parameters=parameters,
            parameter_bindings=lid_bindings,
        ),
        parameters=parameters,
    )


def _circle_joins(
    centers: list[tuple[float, float]],
    *,
    diameter: float,
    z: float,
    length: float,
) -> list[CircleExtrude]:
    return [
        CircleExtrude(
            diameter_mm=diameter,
            x_mm=x_mm,
            y_mm=y_mm,
            z_mm=z,
            length_mm=length,
            operation="join",
        )
        for x_mm, y_mm in centers
    ]


def _circle_cuts(
    centers: list[tuple[float, float]],
    *,
    diameter: float,
    z: float,
    length: float,
    direction: ExtentDirection,
) -> list[CircleExtrude]:
    return [
        CircleExtrude(
            diameter_mm=diameter,
            x_mm=x_mm,
            y_mm=y_mm,
            z_mm=z,
            length_mm=length,
            operation="cut",
            direction=direction,
        )
        for x_mm, y_mm in centers
    ]


def _ensure_rectangle_inside(
    label: str,
    center_x: float,
    center_y: float,
    width: float,
    height: float,
    outer_width: float,
    outer_height: float,
) -> None:
    if center_x - width / 2 < 0 or center_x + width / 2 > outer_width:
        raise InventorValidationError(f"{label} must fit within out_x.")
    if center_y - height / 2 < 0 or center_y + height / 2 > outer_height:
        raise InventorValidationError(f"{label} must fit within out_y.")


def _ensure_point_inside(
    label: str,
    x: float,
    y: float,
    outer_width: float,
    outer_height: float,
    radius: float,
) -> None:
    if x - radius < 0 or x + radius > outer_width:
        raise InventorValidationError(f"{label} must fit within out_x.")
    if y - radius < 0 or y + radius > outer_height:
        raise InventorValidationError(f"{label} must fit within out_y.")


def dew_heater_strap_holder_plan(
    *,
    name: str = "dew_heater_strap_holder",
    lens_r: Real = 42.5,
    gap: Real = 0.5,
    back_thk: Real = 3.0,
    band_w: Real = 25.0,
    sweep: Real = 100.0,
    ch_depth: Real = 2.0,
) -> FeaturePlan:
    """Build the annular-sector dew-heater strap holder."""

    lens_radius = positive_mm("lens_r", lens_r)
    gap_mm = non_negative_mm("gap", gap)
    back_thickness = positive_mm("back_thk", back_thk)
    band_width = positive_mm("band_w", band_w)
    sweep_deg = positive_mm("sweep", sweep)
    channel_depth = positive_mm("ch_depth", ch_depth)
    if sweep_deg >= 360 or channel_depth >= back_thickness:
        raise InventorValidationError("sweep must be below 360 and ch_depth must be below back_thk.")

    inner_radius = lens_radius + gap_mm
    outer_radius = inner_radius + back_thickness
    start_angle = (180 - sweep_deg) / 2
    end_angle = start_angle + sweep_deg
    tab_radius = outer_radius
    operations: list[Operation] = [
        AnnularSectorExtrude(
            inner_radius_mm=inner_radius,
            outer_radius_mm=outer_radius,
            start_angle_deg=start_angle,
            end_angle_deg=end_angle,
            z_mm=0,
            length_mm=band_width,
            operation="join",
        ),
        AnnularSectorExtrude(
            inner_radius_mm=inner_radius,
            outer_radius_mm=inner_radius + channel_depth,
            start_angle_deg=start_angle + 5,
            end_angle_deg=end_angle - 5,
            z_mm=(band_width - 15) / 2,
            length_mm=15,
            operation="cut",
        ),
    ]
    for angle in (start_angle, end_angle):
        import math

        radians = math.radians(angle)
        center_x = tab_radius * math.cos(radians)
        center_y = tab_radius * math.sin(radians)
        operations.extend(
            [
                OrientedRectangleExtrude(
                    width_mm=15,
                    height_mm=3,
                    x_mm=center_x,
                    y_mm=center_y,
                    z_mm=0,
                    length_mm=band_width,
                    angle_deg=angle + 90,
                    operation="join",
                ),
                OrientedRectangleExtrude(
                    width_mm=3,
                    height_mm=4,
                    x_mm=center_x,
                    y_mm=center_y,
                    z_mm=(band_width - 20) / 2,
                    length_mm=20,
                    angle_deg=angle + 90,
                    operation="cut",
                ),
            ]
        )
    import math

    notch_angle = math.radians(start_angle + 5)
    operations.append(
        CircleExtrude(
            diameter_mm=3,
            x_mm=inner_radius * math.cos(notch_angle),
            y_mm=inner_radius * math.sin(notch_angle),
            z_mm=0,
            length_mm=3,
            operation="cut",
        )
    )
    return FeaturePlan(
        name=name,
        operations=operations,
        parameters={
            "lensR": lens_radius,
            "gap": gap_mm,
            "backThk": back_thickness,
            "bandW": band_width,
            "sweep": sweep_deg,
            "chDepth": channel_depth,
            "Ri": inner_radius,
            "Ro": outer_radius,
        },
    )


def encoder_knob_plan(
    *,
    name: str = "encoder_knob",
    knob_d: Real = 18.0,
    knob_h: Real = 15.0,
    bore_d: Real = 6.2,
    bore_depth: Real = 10.0,
    flat_dist: Real = 1.6,
    flute_n: int = 12,
    flute_d: Real = 1.5,
) -> FeaturePlan:
    """Build an EC11 D-shaft encoder knob."""

    diameter = positive_mm("knob_d", knob_d)
    height = positive_mm("knob_h", knob_h)
    bore_diameter = positive_mm("bore_d", bore_d)
    bore_depth_mm = positive_mm("bore_depth", bore_depth)
    flat_distance = numeric_mm("flat_dist", flat_dist)
    flute_diameter = positive_mm("flute_d", flute_d)
    if flute_n < 3 or bore_depth_mm >= height or bore_diameter >= diameter:
        raise InventorValidationError("encoder knob dimensions are inconsistent.")
    operations: list[Operation] = [
        OuterCylinder(diameter_mm=diameter, z_mm=0, length_mm=height),
        CircleExtrude(
            diameter_mm=bore_diameter,
            x_mm=0,
            y_mm=0,
            z_mm=0,
            length_mm=bore_depth_mm,
            operation="cut",
        ),
        RectangleExtrude(
            width_mm=diameter,
            height_mm=diameter / 2 - flat_distance,
            x_mm=0,
            y_mm=(diameter / 2 + flat_distance) / 2,
            z_mm=0,
            length_mm=bore_depth_mm,
            operation="cut",
        ),
    ]
    import math

    for index in range(flute_n):
        angle = math.radians(index * 360 / flute_n)
        operations.append(
            CircleExtrude(
                diameter_mm=flute_diameter,
                x_mm=diameter / 2 * math.cos(angle),
                y_mm=diameter / 2 * math.sin(angle),
                z_mm=0,
                length_mm=height,
                operation="cut",
            )
        )
    operations.append(
        RectangleExtrude(
            width_mm=6,
            height_mm=1.2,
            x_mm=3,
            y_mm=0,
            z_mm=height,
            length_mm=1,
            operation="cut",
            direction="negative",
        )
    )
    return FeaturePlan(
        name=name,
        operations=operations,
        parameters={
            "knobD": diameter,
            "knobH": height,
            "boreD": bore_diameter,
            "boreDepth": bore_depth_mm,
            "flatDist": flat_distance,
            "fluteN": float(flute_n),
            "fluteD": flute_diameter,
        },
    )


def tripod_mount_belt_clip_plan(
    *,
    name: str = "tripod_mount_belt_clip",
    pl_x: Real = 44.0,
    pl_y: Real = 32.0,
    pl_t: Real = 4.0,
    boss_d: Real = 16.0,
    boss_h: Real = 4.0,
    nut_af: Real = 11.2,
    nut_depth: Real = 6.0,
    screw_clearance: Real = 7.0,
    include_mount_holes: bool = True,
    include_belt_clip: bool = True,
) -> FeaturePlan:
    """Build the bolt-on tripod plate and optional PETG belt clip."""

    plate_x = positive_mm("pl_x", pl_x)
    plate_y = positive_mm("pl_y", pl_y)
    plate_t = positive_mm("pl_t", pl_t)
    boss_diameter = positive_mm("boss_d", boss_d)
    boss_height = positive_mm("boss_h", boss_h)
    nut_across_flats = positive_mm("nut_af", nut_af)
    nut_depth_mm = positive_mm("nut_depth", nut_depth)
    screw_clearance_mm = positive_mm("screw_clearance", screw_clearance)
    if nut_depth_mm >= plate_t + boss_height:
        raise InventorValidationError("nut_depth must fit within the boss and plate.")
    import math

    operations: list[Operation] = [
        RectangleExtrude(
            width_mm=plate_x,
            height_mm=plate_y,
            x_mm=plate_x / 2,
            y_mm=plate_y / 2,
            z_mm=0,
            length_mm=plate_t,
            direction="negative",
        ),
        CircleExtrude(
            diameter_mm=boss_diameter,
            x_mm=plate_x / 2,
            y_mm=plate_y / 2,
            z_mm=-plate_t,
            length_mm=boss_height,
            operation="join",
            direction="negative",
        ),
        PolygonExtrude(
            sides=6,
            circumradius_mm=nut_across_flats / math.sqrt(3),
            x_mm=plate_x / 2,
            y_mm=plate_y / 2,
            z_mm=-(plate_t + boss_height),
            length_mm=nut_depth_mm,
            rotation_deg=30,
            operation="cut",
        ),
        CircleExtrude(
            diameter_mm=screw_clearance_mm,
            x_mm=plate_x / 2,
            y_mm=plate_y / 2,
            z_mm=-2,
            length_mm=2,
            operation="cut",
        ),
    ]
    if include_mount_holes:
        for x_mm, y_mm in ((6, 6), (plate_x - 6, 6), (6, plate_y - 6), (plate_x - 6, plate_y - 6)):
            operations.append(
                CircleExtrude(
                    diameter_mm=3.4,
                    x_mm=x_mm,
                    y_mm=y_mm,
                    z_mm=0,
                    length_mm=plate_t + 0.2,
                    operation="cut",
                    direction="negative",
                )
            )
    if include_belt_clip:
        operations.extend(
            [
                RectangleExtrude(
                    width_mm=8,
                    height_mm=24,
                    x_mm=plate_x + 4,
                    y_mm=plate_y / 2,
                    z_mm=-plate_t,
                    length_mm=plate_t,
                    operation="join",
                    direction="negative",
                ),
                RectangleExtrude(
                    width_mm=3,
                    height_mm=24,
                    x_mm=plate_x + 7,
                    y_mm=plate_y / 2,
                    z_mm=-plate_t,
                    length_mm=45,
                    operation="join",
                    direction="negative",
                ),
                RectangleExtrude(
                    width_mm=9,
                    height_mm=24,
                    x_mm=plate_x + 3.5,
                    y_mm=plate_y / 2,
                    z_mm=-plate_t - 45,
                    length_mm=3,
                    operation="join",
                ),
                RectangleExtrude(
                    width_mm=3,
                    height_mm=24,
                    x_mm=plate_x - 0.5,
                    y_mm=plate_y / 2,
                    z_mm=-plate_t - 45,
                    length_mm=10,
                    operation="join",
                ),
            ]
        )
    return FeaturePlan(
        name=name,
        operations=operations,
        parameters={
            "plX": plate_x,
            "plY": plate_y,
            "plT": plate_t,
            "bossD": boss_diameter,
            "bossH": boss_height,
            "nutAF": nut_across_flats,
            "nutDepth": nut_depth_mm,
            "screwClr": screw_clearance_mm,
        },
    )


def astro_controller_accessory_plans(
    **kwargs: Real,
) -> MultiPartPlan:
    """Build C, D, and E accessory part plans with default dimensions."""

    dew = dew_heater_strap_holder_plan(
        lens_r=kwargs.get("lens_r", 42.5),
        gap=kwargs.get("gap", 0.5),
        back_thk=kwargs.get("back_thk", 3.0),
        band_w=kwargs.get("band_w", 25.0),
        sweep=kwargs.get("sweep", 100.0),
        ch_depth=kwargs.get("ch_depth", 2.0),
    )
    knob = encoder_knob_plan(
        knob_d=kwargs.get("knob_d", 18.0),
        knob_h=kwargs.get("knob_h", 15.0),
        bore_d=kwargs.get("bore_d", 6.2),
        bore_depth=kwargs.get("bore_depth", 10.0),
        flat_dist=kwargs.get("flat_dist", 1.6),
        flute_n=int(kwargs.get("flute_n", 12)),
        flute_d=kwargs.get("flute_d", 1.5),
    )
    tripod = tripod_mount_belt_clip_plan()
    return MultiPartPlan(
        name="astro_controller_accessories",
        parts={
            "dew_heater_strap_holder": dew,
            "encoder_knob": knob,
            "tripod_mount_belt_clip": tripod,
        },
        parameters={**dew.parameters, **knob.parameters, **tripod.parameters},
    )


def barn_door_star_tracker_plans(
    *,
    tracking_l: Real = 200.0,
    board_len: Real = 215.0,
    board_w: Real = 90.0,
    board_t: Real = 6.0,
    rib_h: Real = 8.0,
    pin_d: Real = 4.2,
    rod_pitch: Real = 0.7,
) -> MultiPartPlan:
    """Build the four printable parts of the Barn-door star tracker."""

    length_mm = positive_mm("board_len", board_len)
    width_mm = positive_mm("board_w", board_w)
    thickness_mm = positive_mm("board_t", board_t)
    rib_height_mm = positive_mm("rib_h", rib_h)
    pin_diameter = positive_mm("pin_d", pin_d)
    tracking_radius = positive_mm("tracking_l", tracking_l)
    pitch_mm = positive_mm("rod_pitch", rod_pitch)
    if width_mm < 90 or length_mm < 215:
        raise InventorValidationError("Barn-door board dimensions must meet the specified minimums.")

    t1: list[Operation] = [
        RectangleExtrude(
            width_mm=width_mm,
            height_mm=length_mm,
            x_mm=width_mm / 2,
            y_mm=length_mm / 2,
            z_mm=0,
            length_mm=thickness_mm,
        )
    ]
    for x_start in (0.5, 36.5, 72.5):
        t1.append(
            CircleExtrude(
                diameter_mm=10,
                x_mm=x_start,
                y_mm=0,
                z_mm=thickness_mm,
                length_mm=17,
                operation="join",
                plane="YZ",
            )
        )
    t1.append(
        CircleExtrude(
            diameter_mm=pin_diameter,
            x_mm=0,
            y_mm=0,
            z_mm=thickness_mm,
            length_mm=width_mm,
            operation="cut",
            plane="YZ",
        )
    )
    t1.extend(
        [
            RectangleExtrude(
                width_mm=40,
                height_mm=35,
                x_mm=45,
                y_mm=200,
                z_mm=thickness_mm,
                length_mm=4,
            ),
            CircleExtrude(
                diameter_mm=28,
                x_mm=45,
                y_mm=200,
                z_mm=thickness_mm,
                length_mm=4,
                operation="join",
            ),
            CircleExtrude(
                diameter_mm=16,
                x_mm=45,
                y_mm=120,
                z_mm=0,
                length_mm=4,
                operation="join",
                direction="negative",
            ),
            PolygonExtrude(
                sides=6,
                circumradius_mm=11.2 / 3**0.5,
                x_mm=45,
                y_mm=120,
                z_mm=-8,
                length_mm=6,
                operation="cut",
                rotation_deg=30,
            ),
            CircleExtrude(
                diameter_mm=7,
                x_mm=45,
                y_mm=120,
                z_mm=-2,
                length_mm=2,
                operation="cut",
            ),
            CircleExtrude(
                diameter_mm=9,
                x_mm=15,
                y_mm=25,
                z_mm=thickness_mm,
                length_mm=60,
                operation="join",
                plane="YZ",
            ),
            CircleExtrude(
                diameter_mm=5,
                x_mm=15,
                y_mm=25,
                z_mm=thickness_mm,
                length_mm=60,
                operation="cut",
                plane="YZ",
            ),
        ]
    )
    for x_mm in (25, 65):
        t1.append(
            RectangleExtrude(
                width_mm=3,
                height_mm=length_mm - 20,
                x_mm=x_mm,
                y_mm=length_mm / 2,
                z_mm=0,
                length_mm=rib_height_mm,
                operation="join",
                direction="negative",
            )
        )

    t2: list[Operation] = [
        RectangleExtrude(
            width_mm=width_mm,
            height_mm=length_mm,
            x_mm=width_mm / 2,
            y_mm=length_mm / 2,
            z_mm=0,
            length_mm=thickness_mm,
        )
    ]
    for x_start in (18, 54):
        t2.append(
            CircleExtrude(
                diameter_mm=10,
                x_mm=x_start,
                y_mm=0,
                z_mm=thickness_mm,
                length_mm=17,
                operation="join",
                plane="YZ",
            )
        )
    t2.append(
        CircleExtrude(
            diameter_mm=pin_diameter,
            x_mm=18,
            y_mm=0,
            z_mm=thickness_mm,
            length_mm=width_mm - 18,
            operation="cut",
            plane="YZ",
        )
    )
    for x_mm in (39.5, 53.5):
        t2.append(
            RectangleExtrude(
                width_mm=3,
                height_mm=12,
                x_mm=x_mm,
                y_mm=200,
                z_mm=thickness_mm,
                length_mm=12,
            )
        )
    t2.extend(
        [
            CircleExtrude(
                diameter_mm=3.2,
                x_mm=37,
                y_mm=200,
                z_mm=12,
                length_mm=18,
                operation="cut",
                plane="YZ",
            ),
            CircleExtrude(
                diameter_mm=18,
                x_mm=45,
                y_mm=150,
                z_mm=thickness_mm,
                length_mm=6,
                operation="join",
            ),
            PolygonExtrude(
                sides=6,
                circumradius_mm=11.2 / 3**0.5,
                x_mm=45,
                y_mm=150,
                z_mm=12,
                length_mm=6,
                operation="cut",
                direction="negative",
                rotation_deg=30,
            ),
            CircleExtrude(
                diameter_mm=7,
                x_mm=45,
                y_mm=150,
                z_mm=12,
                length_mm=6,
                operation="cut",
                direction="negative",
            ),
        ]
    )
    for x_mm in (25, 65):
        t2.append(
            RectangleExtrude(
                width_mm=3,
                height_mm=length_mm - 20,
                x_mm=x_mm,
                y_mm=length_mm / 2,
                z_mm=0,
                length_mm=rib_height_mm,
                operation="join",
                direction="negative",
            )
        )

    t3: list[Operation] = [
        RectangleExtrude(
            width_mm=20,
            height_mm=12,
            x_mm=45,
            y_mm=200,
            z_mm=0,
            length_mm=16,
        ),
        PolygonExtrude(
            sides=6,
            circumradius_mm=7 / 3**0.5,
            x_mm=45,
            y_mm=200,
            z_mm=16,
            length_mm=3.2,
            operation="cut",
            direction="negative",
            rotation_deg=30,
        ),
        CircleExtrude(
            diameter_mm=4.3,
            x_mm=45,
            y_mm=200,
            z_mm=0,
            length_mm=16,
            operation="cut",
        ),
        CircleExtrude(
            diameter_mm=3,
            x_mm=35,
            y_mm=200,
            z_mm=8,
            length_mm=20,
            operation="cut",
            plane="YZ",
        ),
    ]

    t4: list[Operation] = [
        OuterCylinder(diameter_mm=12, z_mm=0, length_mm=20),
        CircleExtrude(
            diameter_mm=5,
            x_mm=0,
            y_mm=0,
            z_mm=20,
            length_mm=10,
            operation="cut",
            direction="negative",
        ),
        RectangleExtrude(
            width_mm=6,
            height_mm=3,
            x_mm=0,
            y_mm=3.0,
            z_mm=10,
            length_mm=10,
            operation="cut",
            direction="negative",
        ),
        CircleExtrude(
            diameter_mm=3.3,
            x_mm=0,
            y_mm=0,
            z_mm=0,
            length_mm=10,
            operation="cut",
        ),
        CircleExtrude(
            diameter_mm=3,
            x_mm=6,
            y_mm=0,
            z_mm=15,
            length_mm=3,
            operation="cut",
            plane="YZ",
            direction="negative",
        ),
        CircleExtrude(
            diameter_mm=3,
            x_mm=6,
            y_mm=0,
            z_mm=5,
            length_mm=3,
            operation="cut",
            plane="YZ",
            direction="negative",
        ),
    ]

    return MultiPartPlan(
        name="barn_door_star_tracker",
        parts={
            "barn_door_t1_base_board": FeaturePlan(name="barn_door_t1_base_board", operations=t1),
            "barn_door_t2_top_board": FeaturePlan(name="barn_door_t2_top_board", operations=t2),
            "barn_door_t3_drive_nut_block": FeaturePlan(name="barn_door_t3_drive_nut_block", operations=t3),
            "barn_door_t4_stepper_coupler": FeaturePlan(name="barn_door_t4_stepper_coupler", operations=t4),
        },
        parameters={
            "L": tracking_radius,
            "boardLen": length_mm,
            "boardW": width_mm,
            "boardT": thickness_mm,
            "ribH": rib_height_mm,
            "pinD": pin_diameter,
            "rodPitch": pitch_mm,
        },
    )


def bahtinov_focusing_mask_plan(
    *,
    name: str = "bahtinov_focusing_mask",
    d_ap: Real = 51.0,
    focal_length: Real = 360.0,
    factor: Real = 150.0,
    alpha: Real = 20.0,
    mask_t: Real = 1.8,
) -> FeaturePlan:
    """Build a printable, three-grating Bahtinov mask approximation."""

    aperture = positive_mm("d_ap", d_ap)
    focal = positive_mm("f_mm", focal_length)
    factor_mm = positive_mm("f_fac", factor)
    alpha_deg = positive_mm("alpha", alpha)
    thickness = positive_mm("mask_t", mask_t)
    if not 15 <= alpha_deg <= 25:
        raise InventorValidationError("alpha must be between 15 and 25 degrees.")
    period = focal / factor_mm
    slit_width = period / 2
    radius = aperture / 2
    mask_diameter = aperture + 12
    operations: list[Operation] = [
        OuterCylinder(diameter_mm=mask_diameter, z_mm=0, length_mm=thickness)
    ]
    half_slit = slit_width / 2
    inset_radius = radius - half_slit
    y = -inset_radius
    while y <= -half_slit:
        x_limit = max(0.0, (inset_radius**2 - y**2) ** 0.5)
        if x_limit > half_slit:
            operations.append(
                OrientedRectangleExtrude(
                    width_mm=2 * x_limit,
                    height_mm=slit_width,
                    x_mm=0,
                    y_mm=y,
                    z_mm=0,
                    length_mm=thickness,
                    operation="cut",
                )
            )
        y += period
    for angle, quadrant in ((alpha_deg, "left"), (-alpha_deg, "right")):
        for center_x, center_y, line_length in _bahtinov_quarter_segments(
            radius=inset_radius,
            angle_deg=angle,
            period=period,
            slit_width=slit_width,
            quadrant=quadrant,
        ):
            operations.append(
                OrientedRectangleExtrude(
                    width_mm=line_length,
                    height_mm=slit_width,
                    x_mm=center_x,
                    y_mm=center_y,
                    z_mm=0,
                    length_mm=thickness,
                    angle_deg=angle,
                    operation="cut",
                )
            )
    return FeaturePlan(
        name=name,
        operations=operations,
        parameters={
            "D_ap": aperture,
            "f_mm": focal,
            "F_fac": factor_mm,
            "alpha": alpha_deg,
            "maskT": thickness,
            "D_mask": mask_diameter,
            "period": period,
            "slitWidth": slit_width,
        },
    )


def _bahtinov_quarter_segments(
    *,
    radius: float,
    angle_deg: float,
    period: float,
    slit_width: float,
    quadrant: str,
) -> list[tuple[float, float, float]]:
    """Return non-overlapping slit centerlines clipped to one upper quadrant."""

    import math

    angle = math.radians(angle_deg)
    direction_x, direction_y = math.cos(angle), math.sin(angle)
    normal_x, normal_y = -direction_y, direction_x
    inset = slit_width / 2
    segments: list[tuple[float, float, float]] = []

    for offset_index in range(-int(radius / period) - 2, int(radius / period) + 3):
        offset = offset_index * period
        if abs(offset) >= radius:
            continue
        origin_x = normal_x * offset
        origin_y = normal_y * offset
        t_limit = (radius**2 - offset**2) ** 0.5
        t_min, t_max = -t_limit, t_limit

        if quadrant == "left":
            # Keep the complete slit inside x <= 0 and y >= 0.
            bound = (-inset - origin_x) / direction_x
            if direction_x > 0:
                t_max = min(t_max, bound)
            else:
                t_min = max(t_min, bound)
        else:
            bound = (inset - origin_x) / direction_x
            if direction_x > 0:
                t_min = max(t_min, bound)
            else:
                t_max = min(t_max, bound)

        bound = (inset - origin_y) / direction_y
        if direction_y > 0:
            t_min = max(t_min, bound)
        else:
            t_max = min(t_max, bound)

        if t_max - t_min < slit_width:
            continue
        center_t = (t_min + t_max) / 2
        segments.append(
            (
                origin_x + direction_x * center_t,
                origin_y + direction_y * center_t,
                t_max - t_min,
            )
        )
    return segments


def dew_shield_plan(
    *,
    name: str = "dew_shield_lens_hood",
    lens_od: Real = 62.0,
    fit: Real = 0.5,
    wall: Real = 2.0,
    shield_len: Real | None = None,
) -> FeaturePlan:
    """Build a tube-style dew shield with three internal grip ribs."""

    lens_outer = positive_mm("lens_od", lens_od)
    fit_mm = non_negative_mm("fit", fit)
    wall_mm = positive_mm("wall", wall)
    length_mm = positive_mm("shield_len", shield_len if shield_len is not None else lens_outer * 1.2)
    shield_inner = lens_outer + fit_mm
    shield_outer = shield_inner + 2 * wall_mm
    operations: list[Operation] = [
        OuterCylinder(diameter_mm=shield_outer, z_mm=0, length_mm=length_mm),
        DeferredCenterBore(diameter_mm=shield_inner),
        ApplyDeferredBores(),
    ]
    import math

    for angle in (0, 120, 240):
        radians = math.radians(angle)
        rib_radius = shield_inner / 2 - 0.3
        operations.append(
            OrientedRectangleExtrude(
                width_mm=0.6,
                height_mm=3,
                x_mm=rib_radius * math.cos(radians),
                y_mm=rib_radius * math.sin(radians),
                z_mm=0,
                length_mm=min(10, length_mm),
                angle_deg=angle,
                operation="join",
            )
        )
    return FeaturePlan(
        name=name,
        operations=operations,
        parameters={
            "lensOD": lens_outer,
            "fit": fit_mm,
            "wall": wall_mm,
            "shieldID": shield_inner,
            "shieldOD": shield_outer,
            "shieldLen": length_mm,
        },
    )


def power_bank_cradle_plan(
    *,
    name: str = "power_bank_cradle",
    pb_w: Real = 68.0,
    pb_l: Real = 140.0,
    pb_t: Real = 15.0,
    wall: Real = 2.0,
) -> FeaturePlan:
    """Build an open power-bank tray with side strap slots and cable notch."""

    width = positive_mm("pb_w", pb_w)
    length = positive_mm("pb_l", pb_l)
    thickness = positive_mm("pb_t", pb_t)
    wall_mm = positive_mm("wall", wall)
    outer_width = width + 2 * wall_mm
    outer_length = length + 2 * wall_mm
    outer_height = thickness + 6
    operations: list[Operation] = [
        RectangleExtrude(
            width_mm=outer_width,
            height_mm=outer_length,
            x_mm=outer_width / 2,
            y_mm=outer_length / 2,
            z_mm=0,
            length_mm=outer_height,
        ),
        Shell(
            outer_width_mm=outer_width,
            outer_depth_mm=outer_length,
            outer_height_mm=outer_height,
            thickness_mm=wall_mm,
        ),
        RectangleExtrude(
            width_mm=20,
            height_mm=3,
            x_mm=0,
            y_mm=outer_length / 2,
            z_mm=outer_height / 2,
            length_mm=wall_mm,
            operation="cut",
            plane="YZ",
        ),
        RectangleExtrude(
            width_mm=20,
            height_mm=3,
            x_mm=outer_width,
            y_mm=outer_length / 2,
            z_mm=outer_height / 2,
            length_mm=wall_mm,
            operation="cut",
            plane="YZ",
            direction="negative",
        ),
        CircleExtrude(
            diameter_mm=10,
            x_mm=outer_width / 2,
            y_mm=0,
            z_mm=outer_height / 2,
            length_mm=wall_mm,
            operation="cut",
            plane="XZ",
        ),
    ]
    return FeaturePlan(
        name=name,
        operations=operations,
        parameters={"pbW": width, "pbL": length, "pbT": thickness, "wall": wall_mm},
    )


def tripod_leg_clip_plan(
    *,
    name: str = "tripod_leg_clip",
    leg_od: Real = 25.0,
) -> FeaturePlan:
    """Build a snap-on C clip for a tripod leg."""

    leg_outer = positive_mm("leg_od", leg_od)
    inner = leg_outer + 0.5
    outer = inner + 6
    return FeaturePlan(
        name=name,
        operations=[
            AnnularSectorExtrude(
                inner_radius_mm=inner / 2,
                outer_radius_mm=outer / 2,
                start_angle_deg=40,
                end_angle_deg=320,
                z_mm=0,
                length_mm=24,
            ),
            OrientedRectangleExtrude(
                width_mm=20,
                height_mm=3,
                x_mm=outer / 2,
                y_mm=0,
                z_mm=5,
                length_mm=14,
                angle_deg=0,
                operation="join",
            ),
        ],
        parameters={"legOD": leg_outer, "clipID": inner, "clipOD": outer},
    )


def cable_clip_plan(
    *,
    name: str = "cable_clip",
    cable_d: Real = 5.0,
) -> FeaturePlan:
    """Build a small snap-in cable clip."""

    cable = positive_mm("cable_d", cable_d)
    inner = cable / 2
    outer = inner + 3
    return FeaturePlan(
        name=name,
        operations=[
            AnnularSectorExtrude(
                inner_radius_mm=inner,
                outer_radius_mm=outer,
                start_angle_deg=45,
                end_angle_deg=315,
                z_mm=0,
                length_mm=10,
            ),
            OrientedRectangleExtrude(
                width_mm=3,
                height_mm=4,
                x_mm=outer,
                y_mm=0,
                z_mm=3,
                length_mm=4,
                angle_deg=0,
                operation="cut",
            ),
        ],
        parameters={"cableD": cable, "clipID": cable, "clipOD": outer * 2},
    )


def arca_swiss_qr_plate_plan(
    *,
    name: str = "arca_swiss_qr_plate",
    top_w: Real = 38.0,
    chamfer_h: Real = 4.5,
    plate_h: Real = 9.0,
    plate_len: Real = 60.0,
) -> FeaturePlan:
    """Build an Arca-Swiss dovetail plate from the specified XZ profile."""

    top_width = positive_mm("top_w", top_w)
    chamfer = positive_mm("ch_h", chamfer_h)
    height = positive_mm("pl_h", plate_h)
    length = positive_mm("pl_len", plate_len)
    if top_width <= 2 * chamfer or height <= chamfer:
        raise InventorValidationError("Arca plate dimensions are inconsistent.")
    bot_width = top_width - 2 * chamfer
    center_x = top_width / 2
    points = (
        (center_x - top_width / 2, height),
        (center_x + top_width / 2, height),
        (center_x + bot_width / 2, chamfer),
        (center_x + bot_width / 2, 0),
        (center_x - bot_width / 2, 0),
        (center_x - bot_width / 2, chamfer),
    )
    operations: list[Operation] = [
        ProfileExtrude(
            points=points,
            plane="XZ",
            offset_mm=0,
            length_mm=length,
        ),
        RectangleExtrude(
            width_mm=7,
            height_mm=20,
            x_mm=center_x,
            y_mm=30,
            z_mm=height,
            length_mm=height + 0.2,
            operation="cut",
            direction="negative",
        ),
        RectangleExtrude(
            width_mm=12,
            height_mm=20,
            x_mm=center_x,
            y_mm=30,
            z_mm=0,
            length_mm=4,
            operation="cut",
        ),
    ]
    for y_mm in (3, length - 3):
        operations.append(
            CircleExtrude(
                diameter_mm=3.2,
                x_mm=center_x,
                y_mm=y_mm,
                z_mm=height,
                length_mm=height + 0.2,
                operation="cut",
                direction="negative",
            )
        )
    return FeaturePlan(
        name=name,
        operations=operations,
        parameters={
            "topW": top_width,
            "chH": chamfer,
            "botW": bot_width,
            "plH": height,
            "plLen": length,
        },
    )


def astro_kit_addon_plans() -> MultiPartPlan:
    """Build Astro Kit add-on parts F through I."""

    parts = {
        "bahtinov_focusing_mask": bahtinov_focusing_mask_plan(),
        "dew_shield_lens_hood": dew_shield_plan(),
        "power_bank_cradle": power_bank_cradle_plan(),
        "tripod_leg_clip": tripod_leg_clip_plan(),
        "cable_clip": cable_clip_plan(),
        "arca_swiss_qr_plate": arca_swiss_qr_plate_plan(),
    }
    parameters: dict[str, float] = {}
    for part in parts.values():
        parameters.update(part.parameters)
    return MultiPartPlan(name="astro_kit_addons", parts=parts, parameters=parameters)


def micro_drone_frame_plan(
    *,
    name: str = "micro_drone_frame",
    wheelbase: Real = 88.0,
    motor_d: Real = 7.05,
    motor_length: Real = 16.5,
    duct_id: Real = 57.0,
    duct_wall_t: Real = 0.8,
    duct_height: Real = 10.0,
    sides: int = 8,
    arm_t: Real = 2.6,
    arm_w: Real = 4.0,
) -> FeaturePlan:
    """Build a serializable FeaturePlan for an 8-sided angular stealth ducted micro drone frame."""

    import math

    wheelbase_mm = positive_mm("wheelbase", wheelbase)
    motor_diameter_mm = positive_mm("motor_d", motor_d)
    motor_length_mm = positive_mm("motor_length", motor_length)
    duct_inner_d_mm = positive_mm("duct_id", duct_id)
    duct_wall_t_mm = positive_mm("duct_wall_t", duct_wall_t)
    duct_height_mm = positive_mm("duct_height", duct_height)
    arm_thickness_mm = positive_mm("arm_t", arm_t)
    arm_width_mm = positive_mm("arm_w", arm_w)

    operations = [
        PolygonExtrude(
            sides=sides,
            circumradius_mm=14.0,
            x_mm=0.0,
            y_mm=0.0,
            z_mm=-3.0,
            length_mm=4.0,
            operation="join",
        ),
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

    arm_radius = wheelbase_mm / 2.0
    angles_deg = [45.0, 135.0, 225.0, 315.0]

    for angle in angles_deg:
        rad = math.radians(angle)
        mx = arm_radius * math.cos(rad)
        my = arm_radius * math.sin(rad)

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

        pod_od = motor_diameter_mm + 2.4
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
        name=name,
        operations=operations,
        parameters={
            "wb": wheelbase_mm,
            "motorD": motor_diameter_mm,
            "ductID": duct_inner_d_mm,
            "armT": arm_thickness_mm,
        },
    )


def _ensure_circles_do_not_overlap(
    circles: list[tuple[str, float, float, float]],
) -> None:
    for index, (label_a, x_a, y_a, radius_a) in enumerate(circles):
        for label_b, x_b, y_b, radius_b in circles[index + 1 :]:
            distance_squared = (x_b - x_a) ** 2 + (y_b - y_a) ** 2
            if distance_squared < (radius_a + radius_b) ** 2:
                raise InventorValidationError(f"{label_a} and {label_b} must not overlap.")

