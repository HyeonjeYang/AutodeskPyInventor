from __future__ import annotations

import os
from pathlib import Path

import pytest

import autodesk_pyinventor as api


pytestmark = pytest.mark.skipif(
    os.name != "nt" or os.getenv("AUTODESK_PYINVENTOR_RUN_INTEGRATION") != "1",
    reason="Inventor integration tests require Windows, Inventor, and opt-in env var.",
)


def test_inventor_tube(tmp_path: Path) -> None:
    app = api.connect(visible=False)
    path = tmp_path / "tube.ipt"
    part = api.Part.new(app=app, name="tube", path=path)

    part.tube(od=50, id=35, length=120)
    part.save()
    part.close()

    assert path.exists()
