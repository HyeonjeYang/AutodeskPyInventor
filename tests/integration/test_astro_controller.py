from __future__ import annotations

import os
from pathlib import Path

import pytest

import autodesk_pyinventor as api


pytestmark = pytest.mark.skipif(
    os.name != "nt" or os.getenv("AUTODESK_PYINVENTOR_RUN_INTEGRATION") != "1",
    reason="Inventor integration tests require Windows, Inventor, and opt-in env var.",
)


@pytest.mark.inventor
def test_astro_controller_parts_parameters_and_assembly(inventor_tmp_path: Path) -> None:
    app = api.connect(visible=False)
    enclosure = api.astro_controller_enclosure_plan()
    base_path = inventor_tmp_path / "astro_controller_base.ipt"
    lid_path = inventor_tmp_path / "astro_controller_lid.ipt"
    assembly_path = inventor_tmp_path / "astro_controller.iam"

    for feature_plan, path in ((enclosure.base, base_path), (enclosure.lid, lid_path)):
        part = api.Part.from_plan(app=app, plan=feature_plan, path=path)
        part.save()
        part.close()

    assembly_plan = api.EnclosureAssemblyPlan(
        base_input=base_path,
        lid_input=lid_path,
        output=assembly_path,
        base_h_mm=enclosure.parameters["baseH"],
    )
    assembly = api.Assembly.from_plan(app=app, plan=assembly_plan)
    assembly.close()

    part_document_type = int(app.backend.constants.kPartDocumentObject)
    assembly_document_type = int(app.backend.constants.kAssemblyDocumentObject)
    expected_parameters = set(enclosure.parameters)
    driven_parameters = (
        (base_path, {"baseH", "bossH", "wall"}),
        (lid_path, {"lidT", "oledPocketDepth"}),
    )
    for path, expected_driven in driven_parameters:
        document = app.raw.Documents.Open(str(path), False)
        try:
            assert int(document.DocumentType) == part_document_type
            assert int(document.ComponentDefinition.SurfaceBodies.Count) >= 1
            user_parameters = document.ComponentDefinition.Parameters.UserParameters
            actual = {
                str(user_parameters.Item(index).Name)
                for index in range(1, int(user_parameters.Count) + 1)
            }
            assert actual >= expected_parameters
            for name in expected_driven:
                assert int(user_parameters.Item(name).Dependents.Count) >= 1
        finally:
            document.Close(False)

    document = app.raw.Documents.Open(str(assembly_path), False)
    try:
        assert int(document.DocumentType) == assembly_document_type
        assert int(document.ComponentDefinition.Occurrences.Count) == 2
        lid_z_cm = float(document.ComponentDefinition.Occurrences.Item(2).Transformation.Cell(3, 4))
        assert lid_z_cm == pytest.approx(enclosure.parameters["baseH"] / 10)
    finally:
        document.Close(False)
