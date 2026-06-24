from __future__ import annotations

from autodesk_pyinventor.units import cm_to_mm, mm_diameter, mm_radius, mm_to_cm


def test_mm_cm_conversions() -> None:
    assert mm_to_cm(0) == 0
    assert mm_to_cm(10) == 1
    assert mm_to_cm(63.5) == 6.35
    assert mm_to_cm(-10) == -1
    assert cm_to_mm(1.5) == 15


def test_radius_diameter_helpers() -> None:
    assert mm_radius(80) == 40
    assert mm_diameter(12.5) == 25
