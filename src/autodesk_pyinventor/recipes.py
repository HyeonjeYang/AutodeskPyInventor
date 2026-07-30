"""Manufacturing-oriented geometry recipes."""

from __future__ import annotations

from numbers import Real

from .exceptions import InventorValidationError
from .plan import (
    ApplyDeferredBores,
    CircleExtrude,
    DeferredCenterBore,
    EnclosurePlan,
    ExtentDirection,
    FeaturePlan,
    Operation,
    OuterCylinder,
    ParameterBinding,
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
