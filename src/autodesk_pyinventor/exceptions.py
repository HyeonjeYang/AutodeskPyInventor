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


class ValidationError(AutodeskPyInventorError, ValueError):
    """Raised when recipe inputs are invalid."""


class PlanExecutionError(AutodeskPyInventorError):
    """Raised when a FeaturePlan cannot be executed by the backend."""


class ExportError(AutodeskPyInventorError):
    """Raised when an export operation fails."""
