"""Document creation and template helpers."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from uuid import uuid4

from .constants import PART_SUFFIX
from .exceptions import ValidationError
from .validation import path_with_suffix


def ensure_parent_dir(path: Path) -> None:
    """Create the parent directory for a document or export path."""

    path.parent.mkdir(parents=True, exist_ok=True)


def safe_template_copy(template: Path, *, destination_dir: Path | None = None) -> Path:
    """Copy a part template before handing it to Inventor."""

    template = path_with_suffix("template", template, (PART_SUFFIX,))
    if not template.exists():
        raise ValidationError(f"template does not exist: {template}")
    if not template.is_file():
        raise ValidationError(f"template is not a file: {template}")

    target_dir = destination_dir or Path(tempfile.mkdtemp(prefix="autodesk_pyinventor_"))
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{template.stem}-{uuid4().hex}{template.suffix}"
    shutil.copy2(template, target)
    return target


def normalize_part_path(path: Path | None) -> Path | None:
    """Validate an optional Inventor part path."""

    if path is None:
        return None
    return path_with_suffix("path", Path(path), (PART_SUFFIX,))
