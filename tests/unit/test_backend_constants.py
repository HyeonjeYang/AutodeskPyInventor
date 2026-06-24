from __future__ import annotations

from types import SimpleNamespace

import pytest

from autodesk_pyinventor.backend import InventorBackend
from autodesk_pyinventor.exceptions import InventorGeometryError


def test_backend_rejects_missing_inventor_constants() -> None:
    backend = InventorBackend(app=object(), constants=SimpleNamespace())

    with pytest.raises(InventorGeometryError, match="kJoinOperation"):
        backend._constant("kJoinOperation")
