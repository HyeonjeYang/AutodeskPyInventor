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
def test_inventor_flanged_tube(tmp_path: Path) -> None:
    app = api.connect(visible=False)
    path = tmp_path / "flanged_tube.ipt"
    part = api.Part.new(app=app, name="flanged_tube", path=path)

    part.flanged_tube(
        body_od=63.5,
        body_id=56.5,
        body_length=236,
        flange_od=90,
        flange_thickness=8,
        flange_z=0,
    )
    part.save()
    part.close()

    assert path.exists()
