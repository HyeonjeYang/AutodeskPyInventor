# AutodeskPyInventor

Unofficial Windows-only Python automation for Autodesk Inventor through the COM API.

## What is AutodeskPyInventor?

AutodeskPyInventor is an Inventor-safe geometry builder for common generated mechanical parts.
It is millimeter-first, recipe-first, and focused on reliable part generation.

Current recipes:

- disk
- washer
- tube
- flanged tube

## Why this project exists

Inventor COM automation has sharp edges: templates, units, one-indexed collections, sketch planes,
and through-all cuts can all fail in non-obvious ways. This package hides those quirks behind small
Python APIs and deterministic feature plans.

## How it differs from older PyInventor-style wrappers

This is not a broad FreeCAD clone and not a generic wrapper over every Inventor COM object.

Unlike generic COM wrappers, AutodeskPyInventor builds a FeaturePlan first. The plan can be
validated, printed, tested, serialized, and then executed against Inventor. This makes generation
safer and easier to debug, especially when using LLMs or Codex to generate CAD scripts.

## Installation

```powershell
python -m pip install -e ".[dev]"
```

Runtime requirements:

- Windows
- Python 3.10+
- Autodesk Inventor
- pywin32

## Quick start

```python
from pathlib import Path
import autodesk_pyinventor as api

app = api.connect(visible=True)

part = api.Part.new(
    app=app,
    name="washer",
    path=Path(r"C:\temp\washer.ipt"),
)

part.disk(od=80, id=25, thickness=8)
part.save()
part.export_stl(Path(r"C:\temp\washer.stl"))
part.close()
```

## CLI examples

```powershell
autodesk-pyinventor doctor
autodesk-pyinventor doctor --strict

autodesk-pyinventor disk `
  --output C:\temp\washer.ipt `
  --od 80 `
  --id 25 `
  --thickness 8 `
  --stl C:\temp\washer.stl

autodesk-pyinventor tube `
  --output C:\temp\tube.ipt `
  --od 63.5 `
  --id 56.5 `
  --length 236

autodesk-pyinventor flanged-tube `
  --output C:\temp\flanged_tube.ipt `
  --body-od 63.5 `
  --body-id 56.5 `
  --body-length 236 `
  --flange-od 90 `
  --flange-thickness 8 `
  --flange-z 0
```

## Python API examples

```python
part.tube(
    od=63.5,
    id=56.5,
    length=236,
)

part.flanged_tube(
    body_od=63.5,
    body_id=56.5,
    body_length=236,
    flange_od=90,
    flange_thickness=8,
    flange_z=0,
)
```

## Dry-run mode

Dry run validates and prints the plan without starting Inventor.

```powershell
autodesk-pyinventor disk --od 80 --id 25 --thickness 8 --dry-run
autodesk-pyinventor disk --od 80 --id 25 --thickness 8 --dry-run --json
```

Flanged tubes create all outer solids first, then apply the center bore once at the end.

## Known Inventor COM quirks handled by this library

- Uses `win32com.client.gencache.EnsureDispatch("Inventor.Application")`.
- Loads Inventor constants after COM dispatch.
- Copies a standard part template to the output path before opening it.
- Uses `.Item(n)` for Inventor collections.
- Treats WorkPlanes as one-indexed: YZ=1, XZ=2, XY=3.
- Sketches directly on XY when `z=0`.
- Uses offset work planes only for nonzero `z`.
- Builds outer solids before deferred bores.
- Applies the center bore once using a symmetric through-all cut.
- Exports STL through `part_doc.SaveAs(stl_path, True)`.

## Limitations

Out of scope for v0.1:

- full sketch constraint system
- full parametric dimension management
- drawing generation
- STEP translator customization
- thread and coil automation
- arbitrary boolean modeling
- cloud Design Automation
- MCP server
- natural language CAD generation
- GUI

## Testing

Unit tests do not require Inventor:

```powershell
pytest tests/unit
```

Integration tests require Windows, Autodesk Inventor, and explicit opt-in:

```powershell
$env:AUTODESK_PYINVENTOR_RUN_INTEGRATION=1
pytest tests/integration
```

## Troubleshooting

Run:

```powershell
autodesk-pyinventor doctor
```

Use `--strict` when a failing readiness check should return a nonzero exit code.

Common fixes:

- `pywin32 is not installed`: run `python -m pip install pywin32`
- `Inventor COM connection failed`: make sure Autodesk Inventor is installed
- `Constants are unavailable`: try clearing the `win32com` `gen_py` cache
- `Template not found`: pass `--template C:\path\to\Standard.ipt`

## License

MIT License. See [LICENSE](LICENSE).

## Disclaimer: unofficial, not affiliated with Autodesk

AutodeskPyInventor is unofficial. It is not affiliated with, endorsed by, or sponsored by Autodesk.
