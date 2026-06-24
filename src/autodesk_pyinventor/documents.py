"""Document creation and template helpers."""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from uuid import uuid4
from typing import Any

from .constants import PART_SUFFIX
from .exceptions import InventorDocumentError, ValidationError
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


def copy_template_to_part(template: Path, destination: Path) -> Path:
    """Copy a part template directly to a target part path."""

    template_path = path_with_suffix("template", Path(template), (PART_SUFFIX,))
    part_path = path_with_suffix("path", Path(destination), (PART_SUFFIX,))
    if not template_path.exists() or not template_path.is_file():
        raise InventorDocumentError(
            f"Template not found at {template_path}. Pass --template C:\\path\\to\\Standard.ipt."
        )
    if template_path.resolve() == part_path.resolve():
        raise InventorDocumentError("Refusing to use the template path as the output part path.")

    ensure_parent_dir(part_path)
    shutil.copy2(template_path, part_path)
    return part_path


def normalize_part_path(path: Path | None) -> Path | None:
    """Validate an optional Inventor part path."""

    if path is None:
        return None
    return path_with_suffix("path", Path(path), (PART_SUFFIX,))


def require_part_path(path: str | Path | None) -> Path:
    """Validate a required Inventor part path."""

    if path is None:
        raise InventorDocumentError("An output .ipt path is required for Inventor execution.")
    return path_with_suffix("path", Path(path), (PART_SUFFIX,))


def find_standard_part_template(
    app: Any,
    *,
    template: str | Path | None = None,
    constants: Any | None = None,
) -> Path:
    """Find an Inventor part template without modifying it."""

    if template is not None:
        template_path = path_with_suffix("template", Path(template), (PART_SUFFIX,))
        if template_path.exists() and template_path.is_file():
            return template_path
        raise InventorDocumentError(
            f"Template not found at {template_path}. Pass --template C:\\path\\to\\Standard.ipt."
        )

    file_manager_template = _template_from_file_manager(app, constants)
    if file_manager_template is not None:
        return file_manager_template

    for template_dir in _template_directories(app):
        found = _find_template_in_dir(template_dir)
        if found is not None:
            return found

    raise InventorDocumentError(
        "Template not found. Pass --template C:\\path\\to\\Standard.ipt."
    )


def _template_from_file_manager(app: Any, constants: Any | None) -> Path | None:
    file_manager = getattr(app, "FileManager", None)
    if file_manager is None:
        return None

    part_document_type = getattr(constants, "kPartDocumentObject", None)
    candidates: list[tuple[Any, ...]] = []
    if part_document_type is not None:
        candidates.append((part_document_type,))
    candidates.append(())

    for args in candidates:
        try:
            template = file_manager.GetTemplateFile(*args)
        except Exception:
            continue
        if template:
            path = Path(str(template))
            if path.suffix.lower() == PART_SUFFIX and path.exists():
                return path
    return None


def _template_directories(app: Any) -> list[Path]:
    raw_paths: list[str] = []
    file_locations = getattr(app, "FileLocations", None)
    if file_locations is not None:
        raw_paths.append(str(getattr(file_locations, "TemplatesPath", "")))

    design_project_manager = getattr(app, "DesignProjectManager", None)
    active_project = getattr(design_project_manager, "ActiveDesignProject", None)
    if active_project is not None:
        raw_paths.append(str(getattr(active_project, "TemplatesPath", "")))

    directories: list[Path] = []
    for raw_path in raw_paths:
        for part in raw_path.split(";"):
            if part.strip():
                directories.append(Path(part.strip()))
    return directories


def _find_template_in_dir(directory: Path) -> Path | None:
    if not directory.exists() or not directory.is_dir():
        return None

    names = ["Standard.ipt", "standard.ipt", "Standard (mm).ipt", "Metric.ipt", "ISO.ipt"]
    for name in names:
        candidate = directory / name
        if candidate.exists() and candidate.is_file():
            return candidate

    for candidate in directory.rglob("*.ipt"):
        if candidate.is_file():
            return candidate
    return None
