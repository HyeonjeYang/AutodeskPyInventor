"""Manufacturing-oriented geometry recipes."""

from __future__ import annotations

from numbers import Real

from .plan import ApplyDeferredBores, DeferredCenterBore, FeaturePlan, OuterCylinder
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
