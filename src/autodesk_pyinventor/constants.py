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
XY_WORK_PLANE_INDEX = 3

PART_SUFFIX = ".ipt"
ASSEMBLY_SUFFIX = ".iam"
STL_SUFFIX = ".stl"
