"""Package-specific exceptions."""

from __future__ import annotations


class AutodeskPyInventorError(Exception):
    """Base class for package-specific errors."""


class PlatformNotSupportedError(AutodeskPyInventorError):
    """Raised when real Inventor execution is attempted outside Windows."""


class InventorNotInstalledError(AutodeskPyInventorError):
    """Raised when pywin32 or Autodesk Inventor cannot be reached."""


class InventorConnectionError(AutodeskPyInventorError):
    """Raised when the COM connection to Inventor fails."""


class InventorDocumentError(AutodeskPyInventorError):
    """Raised when an Inventor document cannot be created, opened, saved, or closed."""


class InventorGeometryError(AutodeskPyInventorError):
    """Raised when Inventor cannot create a planned geometry operation."""


class InventorValidationError(AutodeskPyInventorError, ValueError):
    """Raised when recipe inputs are invalid."""


class InventorPlanError(AutodeskPyInventorError):
    """Raised when a FeaturePlan is invalid or cannot be executed."""


class InventorExportError(AutodeskPyInventorError):
    """Raised when an export operation fails."""


ValidationError = InventorValidationError
PlanExecutionError = InventorPlanError
ExportError = InventorExportError
