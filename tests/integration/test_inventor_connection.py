from __future__ import annotations

import os
from typing import Any

import pytest

pytestmark = pytest.mark.skipif(
    os.name != "nt" or os.getenv("AUTODESK_PYINVENTOR_RUN_INTEGRATION") != "1",
    reason="Inventor integration tests require Windows, Inventor, and opt-in env var.",
)


@pytest.mark.inventor
def test_inventor_connection(inventor_app: Any) -> None:
    assert inventor_app.raw is not None
