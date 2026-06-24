"""High-level part facade."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .app import InventorApp
from .exceptions import InventorPlanError
from .plan import FeaturePlan
from .recipes import disk_plan, flanged_tube_plan, tube_plan, washer_plan


@dataclass
class Part:
    """High-level part facade that records plans before executing COM calls."""

    app: InventorApp | None
    name: str
    path: Path | None = None
    document: Any | None = None
    template: Path | None = None
    plan: FeaturePlan = field(init=False)
    _executed_operations: int = field(default=0, init=False)

    def __post_init__(self) -> None:
        self.plan = FeaturePlan(name=self.name)

    @classmethod
    def new(
        cls,
        *,
        app: InventorApp,
        name: str,
        path: str | Path,
        template: str | Path | None = None,
    ) -> "Part":
        path_obj = Path(path)
        template_obj = Path(template) if template is not None else None
        document = app.new_part_document(name=name, path=path_obj, template=template_obj)
        return cls(
            app=app,
            name=name,
            path=path_obj,
            document=document,
            template=template_obj,
        )

    @classmethod
    def from_plan(
        cls,
        *,
        app: InventorApp,
        plan: FeaturePlan,
        path: str | Path,
        template: str | Path | None = None,
    ) -> "Part":
        part = cls.new(app=app, name=plan.name, path=path, template=template)
        part.execute(plan)
        return part

    @classmethod
    def dry_run(cls, *, name: str, path: str | Path | None = None) -> "Part":
        return cls(app=None, name=name, path=Path(path) if path is not None else None)

    def apply_plan(self, plan: FeaturePlan) -> None:
        self.plan = self.plan.append_plan(plan)
        if self.app is not None and self.document is not None:
            self.app.backend.execute_plan(self.document, plan)
            self._executed_operations += len(plan.operations)

    def disk(self, *, od: float, id: float = 0, thickness: float = 1) -> None:
        self.apply_plan(disk_plan(name=self.name, od=od, id=id, thickness=thickness))

    def washer(self, *, od: float, id: float, thickness: float) -> None:
        self.apply_plan(washer_plan(name=self.name, od=od, id=id, thickness=thickness))

    def tube(self, *, od: float, id: float, length: float) -> None:
        self.apply_plan(tube_plan(name=self.name, od=od, id=id, length=length))

    def flanged_tube(
        self,
        *,
        body_od: float,
        body_id: float,
        body_length: float,
        flange_od: float,
        flange_thickness: float,
        flange_z: float = 0,
    ) -> None:
        self.apply_plan(
            flanged_tube_plan(
                name=self.name,
                body_od=body_od,
                body_id=body_id,
                body_length=body_length,
                flange_od=flange_od,
                flange_thickness=flange_thickness,
                flange_z=flange_z,
            )
        )

    def execute(self, plan: FeaturePlan | None = None) -> None:
        if plan is not None:
            self.apply_plan(plan)
            return

        if self.app is None:
            raise InventorPlanError("Cannot execute a part without an Inventor app connection.")
        if self.document is None:
            self.document = self.app.new_part_document(
                name=self.name,
                path=self.path,
                template=self.template,
            )

        pending_operations = self.plan.operations[self._executed_operations :]
        if pending_operations:
            pending_plan = FeaturePlan(name=self.plan.name, operations=list(pending_operations))
            self.app.backend.execute_plan(self.document, pending_plan)
            self._executed_operations = len(self.plan.operations)

    def save(self) -> None:
        if self.document is None:
            self.execute()
        if self.app is None or self.document is None:
            raise InventorPlanError("Cannot save a part without an Inventor document.")
        self.app.backend.save_document(self.document)

    def export_stl(self, path: str | Path) -> None:
        if self.document is None:
            self.execute()
        if self.app is None or self.document is None:
            raise InventorPlanError("Cannot export a part without an Inventor document.")
        self.app.backend.export_stl(self.document, path)

    def close(self, *, save_changes: bool = False) -> None:
        if self.app is None or self.document is None:
            return
        self.app.backend.close_document(self.document, save_changes=save_changes)
        self.document = None

    def to_json(self, *, indent: int = 2) -> str:
        return self.plan.to_json(indent=indent)

    def explain(self) -> str:
        return self.plan.explain(path=self.path, template=self.template or "standard.ipt")
