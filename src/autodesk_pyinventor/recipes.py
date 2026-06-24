"""Manufacturing-oriented geometry recipes."""

from __future__ import annotations

from numbers import Real

from .plan import FeaturePlan
from .validation import (
    ensure_not_greater_than,
    ensure_outer_greater_than_inner,
    optional_positive_mm,
    positive_mm,
)


def disk_plan(
    *,
    od: Real,
    thickness: Real,
    id: Real | None = None,
    name: str = "disk",
) -> FeaturePlan:
    """Plan a solid disk, optionally with a deferred center bore."""

    outer_diameter = positive_mm("od", od)
    inner_diameter = optional_positive_mm("id", id)
    depth = positive_mm("thickness", thickness)
    if inner_diameter is not None:
        ensure_outer_greater_than_inner("od", outer_diameter, "id", inner_diameter)

    plan = FeaturePlan(
        name=name,
        metadata={
            "recipe": "disk",
            "od_mm": outer_diameter,
            "id_mm": inner_diameter,
            "thickness_mm": depth,
        },
    ).add_step(
        "base_cylinder",
        {
            "diameter_mm": outer_diameter,
            "depth_mm": depth,
            "label": "outer disk",
        },
    )

    if inner_diameter is not None:
        plan = plan.add_step(
            "center_bore",
            {
                "diameter_mm": inner_diameter,
                "depth_mm": depth,
                "deferred": True,
                "label": "center bore",
            },
            notes=("Bore is deferred until after the base solid exists.",),
        )

    return plan


def washer_plan(*, od: Real, id: Real, thickness: Real, name: str = "washer") -> FeaturePlan:
    """Plan a washer as a disk with a required center bore."""

    plan = disk_plan(od=od, id=id, thickness=thickness, name=name)
    return FeaturePlan(
        name=plan.name,
        steps=plan.steps,
        metadata={**plan.metadata, "recipe": "washer"},
    )


def tube_plan(*, od: Real, id: Real, length: Real, name: str = "tube") -> FeaturePlan:
    """Plan a straight tube with a deferred through bore."""

    outer_diameter = positive_mm("od", od)
    inner_diameter = positive_mm("id", id)
    tube_length = positive_mm("length", length)
    ensure_outer_greater_than_inner("od", outer_diameter, "id", inner_diameter)

    return (
        FeaturePlan(
            name=name,
            metadata={
                "recipe": "tube",
                "od_mm": outer_diameter,
                "id_mm": inner_diameter,
                "length_mm": tube_length,
            },
        )
        .add_step(
            "base_cylinder",
            {
                "diameter_mm": outer_diameter,
                "depth_mm": tube_length,
                "label": "outer tube",
            },
        )
        .add_step(
            "center_bore",
            {
                "diameter_mm": inner_diameter,
                "depth_mm": tube_length,
                "deferred": True,
                "label": "tube bore",
            },
            notes=("Through bore is executed after the outer cylinder.",),
        )
    )


def flanged_tube_plan(
    *,
    od: Real,
    id: Real,
    length: Real,
    flange_od: Real,
    flange_thickness: Real,
    name: str = "flanged_tube",
) -> FeaturePlan:
    """Plan a tube with a single flange at the start face."""

    outer_diameter = positive_mm("od", od)
    inner_diameter = positive_mm("id", id)
    tube_length = positive_mm("length", length)
    flange_diameter = positive_mm("flange_od", flange_od)
    flange_depth = positive_mm("flange_thickness", flange_thickness)

    ensure_outer_greater_than_inner("od", outer_diameter, "id", inner_diameter)
    ensure_outer_greater_than_inner("flange_od", flange_diameter, "od", outer_diameter)
    ensure_not_greater_than("flange_thickness", flange_depth, "length", tube_length)

    return (
        FeaturePlan(
            name=name,
            metadata={
                "recipe": "flanged_tube",
                "od_mm": outer_diameter,
                "id_mm": inner_diameter,
                "length_mm": tube_length,
                "flange_od_mm": flange_diameter,
                "flange_thickness_mm": flange_depth,
                "flange_position": "start",
            },
        )
        .add_step(
            "base_cylinder",
            {
                "diameter_mm": outer_diameter,
                "depth_mm": tube_length,
                "label": "outer tube",
            },
        )
        .add_step(
            "flange_cylinder",
            {
                "diameter_mm": flange_diameter,
                "depth_mm": flange_depth,
                "label": "start flange",
            },
            notes=("Flange is joined before the bore is cut.",),
        )
        .add_step(
            "center_bore",
            {
                "diameter_mm": inner_diameter,
                "depth_mm": tube_length,
                "deferred": True,
                "label": "tube and flange bore",
            },
            notes=("Bore is intentionally last to avoid profile ambiguity.",),
        )
    )
