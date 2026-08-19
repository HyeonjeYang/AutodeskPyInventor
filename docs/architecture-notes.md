# Architecture notes

Working notes on known rough edges and possible follow-up work. Items marked
Implemented have landed; the rest are proposals only.

## COM connection reuses a running Inventor instance (Implemented)

`InventorBackend.connect()` (`src/autodesk_pyinventor/backend.py`) now tries
`GetActiveObject` first, before `EnsureDispatch` / dynamic `Dispatch`. This
avoids spawning a second Inventor process, or paying the `EnsureDispatch`
cache-rebuild cost, when Inventor is already open.

## Generalized multi-part assembly plan (Proposed, not implemented)

`EnclosureAssemblyPlan` (`src/autodesk_pyinventor/assembly.py`) only places a
Base at the origin and a Lid at a fixed Z offset. A more general
`AssemblyPlan` built from a list of `OccurrencePlan(part_path, name,
translation_mm, rotation_deg)` entries would support arbitrary occurrence
counts and Z-axis rotation, reusing the existing `CastTo(doc,
"AssemblyDocument")` pattern already used elsewhere in the codebase. Not
implemented because no recipe currently needs more than two occurrences.

## `allow_standalone_cut` on `FeaturePlan.validate()` (Proposed, not implemented)

`FeaturePlan.validate()` (`src/autodesk_pyinventor/plan.py`) currently
rejects any plan whose first solid-affecting operation is a cut. An optional
`allow_standalone_cut: bool = False` parameter, seeding `has_solid` to that
value, would let a plan describe cut-only operations meant to run against an
already-solid document (e.g. modifying an imported part). Backward
compatible, but skipped for now since nothing in `recipes.py` needs it yet.

## Pattern replication helpers (Proposed, not implemented)

Some recipes (e.g. the barn-door star tracker rack teeth) place many
extrudes on a circle or line by repeating sin/cos math by hand. A
`CircularPattern`/`RectangularPattern` operation could replace that
repetition. Left undone because it needs a concrete design for how a
pattern references its "seed" operation(s) in the existing `Operation`
union.
