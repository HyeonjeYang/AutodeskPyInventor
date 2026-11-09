"""Package constants."""

from __future__ import annotations

PACKAGE_NAME = "autodesk-pyinventor"
IMPORT_PACKAGE_NAME = "autodesk_pyinventor"
PROJECT_NAME = "AutodeskPyInventor"

PUBLIC_UNIT = "mm"
INVENTOR_INTERNAL_LENGTH_UNIT = "cm"
MM_PER_CM = 10.0

WINDOWS_OS_NAME = "nt"
INVENTOR_PROG_ID = "Inventor.Application"

# Inventor enum values used by the narrow COM backend. These are intentionally
# limited to the operations this library supports.
PART_DOCUMENT_TYPE = 12290
ASSEMBLY_DOCUMENT_TYPE = 12291
JOIN_OPERATION = 20481
CUT_OPERATION = 20482
POSITIVE_EXTENT_DIRECTION = 20993
NEGATIVE_EXTENT_DIRECTION = 20994
SYMMETRIC_EXTENT_DIRECTION = 20995
XY_WORK_PLANE_INDEX = 3
CIRCLE_CURVE_TYPE = 5124
FILE_BROWSE_IO_MECHANISM = 13059

# Inventor's STL export translator add-in and the option values it accepts.
# Verified against Inventor 2026: ExportUnits 2=inch, 4=cm, 5=mm;
# Resolution 0=high, 1=medium, 2=low.
STL_TRANSLATOR_ADDIN_ID = "{533E9A98-FC3B-11D4-8E7E-0010B541CD80}"
STL_EXPORT_UNITS_MM = 5
STL_RESOLUTION_VALUES = {"high": 0, "medium": 1, "low": 2}

PART_SUFFIX = ".ipt"
ASSEMBLY_SUFFIX = ".iam"
STL_SUFFIX = ".stl"
