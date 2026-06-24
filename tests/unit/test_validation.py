from __future__ import annotations

from pathlib import Path

import pytest

from autodesk_pyinventor.exceptions import ValidationError
from autodesk_pyinventor.validation import (
    ensure_outer_greater_than_inner,
    path_with_suffix,
    positive_mm,
)


def test_positive_mm_accepts_numbers() -> None:
    assert positive_mm("od", 80) == 80.0


@pytest.mark.parametrize("value", [0, -1, True, float("inf")])
def test_positive_mm_rejects_invalid_values(value: float) -> None:
    with pytest.raises(ValidationError):
        positive_mm("od", value)


def test_outer_diameter_must_exceed_inner_diameter() -> None:
    with pytest.raises(ValidationError):
        ensure_outer_greater_than_inner("od", 20, "id", 20)


def test_path_suffix_validation() -> None:
    assert path_with_suffix("path", Path("part.ipt"), (".ipt",)) == Path("part.ipt")
    with pytest.raises(ValidationError):
        path_with_suffix("path", Path("part.step"), (".ipt",))
