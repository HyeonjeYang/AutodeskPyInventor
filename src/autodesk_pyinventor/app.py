"""Application connection helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .backend import InventorBackend


@dataclass
class InventorApp:
    """Connected Autodesk Inventor application wrapper."""

    backend: InventorBackend
    visible: bool = True

    @property
    def raw(self) -> Any:
        """Return the underlying COM application object."""

        return self.backend.app

    def new_part_document(
        self,
        *,
        name: str,
        path: str | Path | None,
        template: str | Path | None = None,
    ) -> Any:
        return self.backend.new_part_document(name=name, path=path, template=template)


def connect(*, visible: bool = True) -> InventorApp:
    """Connect to Autodesk Inventor through COM."""

    return InventorApp(backend=InventorBackend.connect(visible=visible), visible=visible)
