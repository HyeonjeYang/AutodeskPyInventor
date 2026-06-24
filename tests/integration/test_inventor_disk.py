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
def test_inventor_disk(inventor_tmp_path: Path) -> None:
    app = api.connect(visible=False)
    path = inventor_tmp_path / "disk.ipt"
    part = api.Part.new(app=app, name="disk", path=path)

    part.disk(od=80, id=25, thickness=8)
    part.save()
    part.close()

    assert path.exists()
