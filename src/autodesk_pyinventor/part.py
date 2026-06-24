"""High-level part facade."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .app import InventorApp
from .exceptions import PlanExecutionError
from .plan import FeaturePlan
from .recipes import disk_plan, flanged_tube_plan, tube_plan, washer_plan


@dataclass
class Part:
    """High-level part facade that records plans before executing COM calls."""

    app: InventorApp | None
    name: str
    path: Path | None = None
    document: Any | None = None
    plan: FeaturePlan = field(init=False)
    _executed_steps: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.plan = FeaturePlan(name=self.name, metadata={"part_name": self.name})

    @classmethod
    def new(
        cls,
        *,
        app: InventorApp | None = None,
        name: str,
        path: Path | None = None,
        template: Path | None = None,
        dry_run: bool = False,
    ) -> "Part":
        document = None
        if app is not None and not dry_run:
            document = app.new_part_document(name=name, path=path, template=template)
        return cls(app=app if not dry_run else None, name=name, path=path, document=document)

    @classmethod
    def dry_run(cls, *, name: str, path: Path | None = None) -> "Part":
        return cls(app=None, name=name, path=path)

    def apply_plan(self, plan: FeaturePlan) -> "Part":
        self.plan = self.plan.append_plan(plan)
        if self.app is not None and self.document is not None:
            self.app.backend.execute_plan(self.document, plan)
            self._executed_steps += len(plan.steps)
        return self

    def disk(self, *, od: float, thickness: float, id: float | None = None) -> "Part":
        return self.apply_plan(disk_plan(od=od, id=id, thickness=thickness, name=self.name))

    def washer(self, *, od: float, id: float, thickness: float) -> "Part":
        return self.apply_plan(washer_plan(od=od, id=id, thickness=thickness, name=self.name))

    def tube(self, *, od: float, id: float, length: float) -> "Part":
        return self.apply_plan(tube_plan(od=od, id=id, length=length, name=self.name))

    def flanged_tube(
        self,
        *,
        od: float,
        id: float,
        length: float,
        flange_od: float,
        flange_thickness: float,
    ) -> "Part":
        return self.apply_plan(
            flanged_tube_plan(
                od=od,
                id=id,
                length=length,
                flange_od=flange_od,
                flange_thickness=flange_thickness,
                name=self.name,
            )
        )

    def execute(self, *, app: InventorApp | None = None) -> "Part":
        if app is not None:
            self.app = app
        if self.app is None:
            raise PlanExecutionError("Cannot execute a part without an Inventor app connection.")
        if self.document is None:
            self.document = self.app.new_part_document(name=self.name, path=self.path)

        pending_steps = self.plan.steps[self._executed_steps :]
        if pending_steps:
            pending_plan = FeaturePlan(
                name=self.plan.name,
                steps=pending_steps,
                metadata=dict(self.plan.metadata),
            )
            self.app.backend.execute_plan(self.document, pending_plan)
            self._executed_steps = len(self.plan.steps)
        return self

    def save(self, path: Path | None = None) -> None:
        if self.document is None:
            self.execute()
        if self.app is None or self.document is None:
            raise PlanExecutionError("Cannot save a part without an Inventor document.")
        save_path = path or self.path
        self.app.backend.save_document(self.document, save_path)

    def export_stl(self, path: Path) -> None:
        if self.document is None:
            self.execute()
        if self.app is None or self.document is None:
            raise PlanExecutionError("Cannot export a part without an Inventor document.")
        self.app.backend.export_stl(self.document, path)

    def close(self, *, save_changes: bool = False) -> None:
        if self.app is None or self.document is None:
            return
        self.app.backend.close_document(self.document, save_changes=save_changes)
        self.document = None

    def to_json(self, *, indent: int = 2) -> str:
        return self.plan.to_json(indent=indent)
