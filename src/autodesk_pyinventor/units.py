"""Unit conversion helpers."""

from __future__ import annotations

from .constants import MM_PER_CM


def mm_to_cm(value_mm: float) -> float:
    """Convert millimeters to Inventor's internal centimeter length unit."""

    return float(value_mm) / MM_PER_CM


def cm_to_mm(value_cm: float) -> float:
    """Convert Inventor's internal centimeter length unit to millimeters."""

    return float(value_cm) * MM_PER_CM


def mm_radius(diameter_mm: float) -> float:
    """Return a radius in millimeters for a diameter in millimeters."""

    return float(diameter_mm) / 2.0


def mm_diameter(radius_mm: float) -> float:
    """Return a diameter in millimeters for a radius in millimeters."""

    return float(radius_mm) * 2.0
