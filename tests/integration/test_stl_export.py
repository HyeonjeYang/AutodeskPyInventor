from __future__ import annotations

import os

import pytest

import autodesk_pyinventor as api


pytestmark = pytest.mark.skipif(
    os.name != "nt" or os.getenv("AUTODESK_PYINVENTOR_RUN_INTEGRATION") != "1",
    reason="Inventor integration tests require Windows, Inventor, and opt-in env var.",
)


def test_stl_export(tmp_path) -> None:  # type: ignore[no-untyped-def]
    app = api.connect(visible=False)
    part_path = tmp_path / "washer.ipt"
    stl_path = tmp_path / "washer.stl"
    part = api.Part.new(app=app, name="washer", path=part_path)

    part.washer(od=80, id=25, thickness=8)
    part.save()
    part.export_stl(stl_path)
    part.close()

    assert stl_path.exists()
