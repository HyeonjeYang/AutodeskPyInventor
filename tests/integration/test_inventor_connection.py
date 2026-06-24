from __future__ import annotations

import os

import pytest

import autodesk_pyinventor as api


pytestmark = pytest.mark.skipif(
    os.name != "nt" or os.getenv("AUTODESK_PYINVENTOR_RUN_INTEGRATION") != "1",
    reason="Inventor integration tests require Windows, Inventor, and opt-in env var.",
)


def test_inventor_connection() -> None:
    app = api.connect(visible=False)

    assert app.raw is not None
