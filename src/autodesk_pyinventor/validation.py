"""Input validation helpers."""

from __future__ import annotations

import math
from numbers import Real
from pathlib import Path
from typing import Iterable

from .exceptions import InventorValidationError


def numeric_mm(name: str, value: Real) -> float:
    """Return a finite numeric value as float."""

    if isinstance(value, bool) or not isinstance(value, Real):
        raise InventorValidationError(f"{name}={value!r} must be a number in millimeters.")
    result = float(value)
    if not math.isfinite(result):
        raise InventorValidationError(f"{name}={value!r} must be finite.")
    return result


def positive_mm(name: str, value: Real) -> float:
    """Return a finite positive millimeter value."""

    result = numeric_mm(name, value)
    if result <= 0:
        raise InventorValidationError(f"{name}={result:g} must be greater than 0 mm.")
    return result


def non_negative_mm(name: str, value: Real) -> float:
    """Return a finite non-negative millimeter value."""

    result = numeric_mm(name, value)
    if result < 0:
        raise InventorValidationError(f"{name}={result:g} must be greater than or equal to 0 mm.")
    return result


def optional_positive_mm(name: str, value: Real | None) -> float | None:
    """Return None or a finite positive millimeter value."""

    if value is None:
        return None
    return positive_mm(name, value)


def ensure_outer_greater_than_inner(
    outer_name: str,
    outer: float,
    inner_name: str,
    inner: float,
) -> None:
    """Validate that an outer diameter is larger than an inner diameter."""

    if inner >= outer:
        raise InventorValidationError(
            f"{inner_name}={inner:g} must be smaller than {outer_name}={outer:g}."
        )


def ensure_at_least(name: str, value: float, minimum_name: str, minimum: float) -> None:
    """Validate that a value is greater than or equal to a minimum."""

    if value < minimum:
        raise InventorValidationError(
            f"{name}={value:g} must be greater than or equal to {minimum_name}={minimum:g}."
        )


def ensure_not_greater_than(name: str, value: float, limit_name: str, limit: float) -> None:
    """Validate that a value does not exceed a limit."""

    if value > limit:
        raise InventorValidationError(
            f"{name}={value:g} must not be greater than {limit_name}={limit:g}."
        )


def path_with_suffix(name: str, path: Path, suffixes: Iterable[str]) -> Path:
    """Validate a path suffix and return the path."""

    normalized = {suffix.lower() for suffix in suffixes}
    if path.suffix.lower() not in normalized:
        expected = ", ".join(sorted(normalized))
        raise InventorValidationError(f"{name}={path} must use one of these suffixes: {expected}.")
    return path
