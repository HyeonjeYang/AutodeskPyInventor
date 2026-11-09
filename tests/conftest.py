from __future__ import annotations

import shutil
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any
from uuid import uuid4

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(scope="session")
def inventor_app() -> Iterator[Any]:
    """One hidden Inventor session for all integration tests, quit afterwards.

    A hidden Inventor launched over COM is never reused and outlives Python, so
    connecting per test would leave one orphan Inventor.exe behind per test.
    """

    import autodesk_pyinventor as api

    app = api.connect(visible=False)
    try:
        yield app
    finally:
        app.quit_if_launched()


@pytest.fixture
def inventor_tmp_path() -> Iterator[Path]:
    path = Path("C:/tmp/autodesk_pyinventor_tests") / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
