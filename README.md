# AutodeskPyInventor

Unofficial Windows-only Python automation for Autodesk Inventor through the COM API.

Every recipe first builds a validated, serializable `FeaturePlan`, so plans can be
inspected, unit-tested, and dry-run without Inventor installed. Only real part/assembly
generation and STL export need Windows, Inventor, and `pywin32`.

## Install

```powershell
python -m pip install -e ".[dev]"
```

## Run

```powershell
autodesk-pyinventor disk --od 80 --id 25 --thickness 8 --output generated\washer.ipt
autodesk-pyinventor doctor --strict
```

Run any subcommand with `--dry-run --json` to print the plan without starting Inventor.
Available subcommands: `disk`, `washer`, `tube`, `flanged-tube`, `astro-controller-enclosure`,
`astro-controller-assembly`, `astro-controller-accessories`, `barn-door-star-tracker`,
`astro-kit-addons`, `doctor`.

## Contents

- `src/autodesk_pyinventor/` — library: `plan.py` (geometry AST), `backend.py` (COM
  execution), `recipes.py` (parametric part/assembly recipes), `cli.py`.
- `examples/` — short single-file scripts showing library usage.
- `projects/` — larger demo projects (multi-part builds, FEA reports, print/assembly guides).
- `scripts/` — maintenance utilities (not part of the installed package).
- `docs/` — design notes, Inventor COM quirks, troubleshooting, architecture notes.
- `tests/` — `unit/` (no Inventor required) and `integration/` (opt-in, needs Inventor).

## Test

```powershell
pytest
$env:AUTODESK_PYINVENTOR_RUN_INTEGRATION=1
pytest tests\integration
```

See `docs/troubleshooting.md` if `doctor` reports a problem.

MIT License. Not affiliated with or endorsed by Autodesk.
