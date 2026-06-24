from __future__ import annotations

import json
from typing import cast

import pytest

from autodesk_pyinventor.exceptions import ValidationError
from autodesk_pyinventor.plan import FeaturePlan, FeatureStep, JsonValue
from autodesk_pyinventor.recipes import disk_plan, tube_plan


def test_feature_plan_round_trips_json() -> None:
    plan = disk_plan(od=80, id=25, thickness=8, name="washer")

    restored = FeaturePlan.from_json(plan.to_json())

    assert restored == plan
    assert json.loads(restored.to_json())["name"] == "washer"


def test_step_rejects_empty_action() -> None:
    with pytest.raises(ValidationError):
        FeatureStep(action="")


def test_plan_append_tracks_recipe_history() -> None:
    base = FeaturePlan(name="part")
    combined = base.append_plan(disk_plan(od=80, thickness=8)).append_plan(
        tube_plan(od=50, id=25, length=60)
    )

    assert combined.metadata["recipe_history"] == ["disk", "tube"]
    assert len(combined.steps) == 3


def test_plan_rejects_non_json_metadata() -> None:
    bad_metadata = cast(dict[str, JsonValue], {"bad": object()})
    with pytest.raises(ValidationError):
        FeaturePlan(name="bad", metadata=bad_metadata)
