from __future__ import annotations

import shutil
import sys
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import pytest


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture
def inventor_tmp_path() -> Iterator[Path]:
    path = Path("C:/tmp/autodesk_pyinventor_tests") / uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
