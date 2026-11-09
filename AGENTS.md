# AGENTS.md

Working rules for AI coding agents (and humans) changing this repository. Inventor
COM details live in [docs/quirks.md](docs/quirks.md); read it before touching
`backend.py`.

## How the code is shaped

- Plan first: recipes build a `FeaturePlan` (`plan.py`) that validates offline;
  `InventorBackend` (`backend.py`) executes it in one pass.
- The public unit is mm. Convert to Inventor's internal cm only in the backend, with
  `units.mm_to_cm` / `units.cm_to_mm`.
- Geometry the existing operations cannot express (e.g. a chamfer) gets a new plan
  operation (dataclass, `to_dict`, `operation_from_dict`, `explain`, plan validation),
  a backend executor, and unit tests. Recipes never call raw COM.
- `ParameterBinding` targets (`extent`, `diameter`, `distance`) drive the saved `.ipt`
  through its user parameters. Sketch on origin planes when a value must stay editable:
  offset work planes are fixed numbers.

## Verify, don't assume

- Run `pytest` and `--dry-run` before starting Inventor.
- After an Inventor run, measure the result: body count, exact range box, and the
  exported STL's bounding box. A cm-scale STL is 10x too small and still "succeeds".
- Re-open a saved `.ipt` to check what was actually written to disk.
- Live tests: `$env:AUTODESK_PYINVENTOR_RUN_INTEGRATION=1; pytest tests\integration`.
  They share one hidden Inventor session and quit it at the end.

## Inventor sessions

- `connect()` reuses a running, visible Inventor; otherwise it launches one. Quit what
  you launched with `app.quit_if_launched()`: a hidden launched instance is never
  reused and outlives Python, so repeated runs pile up `Inventor.exe` processes.
- Never hide, quit, or kill an Inventor you did not start; it may hold unsaved work.
- Probe unfamiliar COM APIs on a throwaway part in a temp directory, close every
  document you open, and quit the instance afterwards.

## Repository conventions

- `generated/`, CAD outputs (`*.ipt`, `*.stl`, ...) and `projects/*` other than
  `micro_drone_project` are git-ignored on purpose; do not force-add them.
- `ruff check src tests` reports pre-existing findings; do not add new ones (compare
  against `HEAD`).
- Commit messages are a single line.
