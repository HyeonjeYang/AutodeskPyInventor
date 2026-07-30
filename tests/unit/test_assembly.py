from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from autodesk_pyinventor.assembly import EnclosureAssemblyPlan
from autodesk_pyinventor.exceptions import InventorPlanError


def test_assembly_plan_places_lid_at_base_height() -> None:
    plan = EnclosureAssemblyPlan(base_h_mm=29.5)

    assert plan.base_translation_mm == (0, 0, 0)
    assert plan.lid_translation_mm == (0, 0, 29.5)


def test_assembly_plan_json_round_trip() -> None:
    plan = EnclosureAssemblyPlan(
        base_input=Path("generated/base.ipt"),
        lid_input=Path("generated/lid.ipt"),
        output=Path("generated/enclosure.iam"),
        base_h_mm=31,
    )

    restored = EnclosureAssemblyPlan.from_json(plan.to_json())

    assert restored == plan
    assert json.loads(plan.to_json())["occurrences"][1]["translation"] == [0.0, 0.0, 31]


def test_assembly_plan_requires_paths_for_execution() -> None:
    with pytest.raises(InventorPlanError, match="--base-input"):
        EnclosureAssemblyPlan().validate_for_execution()


def test_assembly_execution_uses_set_translation(tmp_path: Path) -> None:
    base = tmp_path / "base.ipt"
    lid = tmp_path / "lid.ipt"
    base.touch()
    lid.touch()
    output = tmp_path / "enclosure.iam"
    translations: list[tuple[float, float, float]] = []
    occurrence_paths: list[str] = []

    class Matrix:
        def SetTranslation(self, vector: tuple[float, float, float]) -> None:
            translations.append(vector)

    class TransientGeometry:
        def CreateMatrix(self) -> Matrix:
            return Matrix()

        def CreateVector(self, x: float, y: float, z: float) -> tuple[float, float, float]:
            return (x, y, z)

    class Occurrences:
        def Add(self, path: str, matrix: Matrix) -> object:
            occurrence_paths.append(path)
            return object()

    document = SimpleNamespace(
        ComponentDefinition=SimpleNamespace(Occurrences=Occurrences()),
        SaveAs=lambda path, copy: None,
    )
    backend = SimpleNamespace(
        new_assembly_document=lambda: document,
        close_document=lambda document, save_changes: None,
    )
    app = SimpleNamespace(
        backend=backend,
        raw=SimpleNamespace(TransientGeometry=TransientGeometry()),
    )
    plan = EnclosureAssemblyPlan(
        base_input=base,
        lid_input=lid,
        output=output,
        base_h_mm=29.5,
    )

    from autodesk_pyinventor.assembly import Assembly

    assembly = Assembly.from_plan(app=app, plan=plan)

    assert translations == [(0.0, 0.0, 0.0), (0.0, 0.0, 2.95)]
    assert occurrence_paths == [str(base.resolve()), str(lid.resolve())]
    assembly.close()
