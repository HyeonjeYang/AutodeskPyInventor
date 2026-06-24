"""Export helpers."""

from __future__ import annotations

from pathlib import Path

from .constants import STL_SUFFIX
from .validation import path_with_suffix


def stl_path(path: Path) -> Path:
    """Validate an STL export path."""

    return path_with_suffix("path", Path(path), (STL_SUFFIX,))
