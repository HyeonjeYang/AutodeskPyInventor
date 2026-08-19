# AutodeskPyInventor

**Reliability-first Python automation for Autodesk Inventor, built for both humans and AI coding agents.**

Every CAD recipe first builds a validated, serializable `FeaturePlan`. Plans can be inspected, unit-tested, and dry-run **without Inventor installed** — only real part/assembly generation and STL export need Windows + Inventor.

---

## Quickstart

```powershell
git clone https://github.com/HyeonjeYang/AutodeskPyInventor.git
cd AutodeskPyInventor
python -m pip install -e ".[dev]"
```

Check that your machine is ready (works even without Inventor open):

```powershell
autodesk-pyinventor doctor --strict
```

Generate a washer (OD 80mm, ID 25mm, thickness 8mm) as a native `.ipt` and a 3D-printable `.stl`:

```powershell
autodesk-pyinventor disk --od 80 --id 25 --thickness 8 --output generated\washer.ipt --stl generated\washer.stl
```

Add `--dry-run --json` to any command to print the plan as JSON without starting Inventor:

```powershell
autodesk-pyinventor disk --od 80 --id 25 --thickness 8 --dry-run --json
```

> **Requirements:** Windows + Autodesk Inventor for real part generation. Python 3.10+ everywhere else (planning, validation, and `pytest` all run cross-platform).

### Try a full example

[projects/micro_drone_project/](projects/micro_drone_project/) is a complete real-world build (frame, motors, propellers, electronics, and assembly) generated entirely through this library. See its [PRINT_AND_ASSEMBLY.md](projects/micro_drone_project/PRINT_AND_ASSEMBLY.md) for the build script commands and print/assembly steps.

---

## Built-in CLI Commands

| Command | Description |
| :--- | :--- |
| `doctor` | Diagnose local Inventor COM, Python, and template readiness |
| `disk` / `washer` | Generate solid disks or bored washers |
| `tube` | Generate straight hollow tubes |
| `flanged-tube` | Generate tubes with mounting flanges |
| `barn-door-star-tracker` | Generate a barn-door star tracker part set |
| `astro-kit-addons` | Generate add-on parts for the Astro Kit |

Run `autodesk-pyinventor <command> --help` for each command's full argument list.

---

## Built for AI Coding Agents

Raw CAD COM APIs are stateful and brittle — an easy way for an LLM-driven script to hang or crash Inventor mid-run. AutodeskPyInventor avoids that with a declarative, functional layer:

1. **Plain-data plans**: agents compose immutable dataclasses (`RectangleExtrude`, `CircleExtrude`, `PolygonExtrude`, ...) instead of calling raw COM methods.
2. **Offline validation**: geometry math, clearances, and JSON plans validate in milliseconds via `pytest` or `--dry-run` — no Inventor required, safe for CI/sandboxes.
3. **Single-pass execution**: once validated, `InventorBackend` executes the whole plan in one reliable pass.

```python
from autodesk_pyinventor.plan import FeaturePlan, CircleExtrude, RectangleExtrude
from autodesk_pyinventor.part import Part
from autodesk_pyinventor.app import connect

# 1. Compose a declarative plan
plan = FeaturePlan(
    name="sensor_mount",
    operations=[
        RectangleExtrude(width_mm=40.0, height_mm=30.0, x_mm=0, y_mm=0, z_mm=0, length_mm=5.0, operation="join"),
        CircleExtrude(diameter_mm=12.0, x_mm=0, y_mm=0, z_mm=-0.5, length_mm=6.0, operation="cut"),
    ],
)

# 2. Validate offline, no Inventor needed
plan.validate()

# 3. Execute in one pass
app = connect(visible=True)
part = Part.from_plan(app=app, plan=plan, path="generated/sensor_mount.ipt")
part.save()
part.export_stl("generated/sensor_mount.stl")
```

---

## Testing

```powershell
# Fast offline unit tests (no Inventor required)
pytest

# Live Inventor COM integration tests (Windows + Inventor only)
$env:AUTODESK_PYINVENTOR_RUN_INTEGRATION=1
pytest tests\integration
```

See [docs/troubleshooting.md](docs/troubleshooting.md) if `doctor` reports a problem.

---

## Repository Layout

- [src/autodesk_pyinventor/](src/autodesk_pyinventor/) — the library: `plan.py` (geometry AST), `backend.py` (COM execution), `recipes.py` (parametric recipes), `cli.py`.
- [examples/](examples/) — short single-file usage scripts.
- [projects/micro_drone_project/](projects/micro_drone_project/) — a full demo build (multi-part, assembly, print guide).
- [docs/](docs/) — design notes, Inventor COM quirks, troubleshooting, architecture notes.
- [tests/](tests/) — `unit/` (no Inventor required) and `integration/` (opt-in, needs Inventor).

---

## Security Notes

- No secrets, credentials, or telemetry are used anywhere in this project.
- Generated CAD artifacts (`.ipt`, `.iam`, `.stl`, etc.) and the `generated/` folder are git-ignored — nothing you build locally gets committed.
- This library only automates the local Inventor COM application; it makes no network calls.

---

## License & Disclaimer

MIT License. Copyright (c) 2026 HyeonjeYang.

*Not affiliated with, endorsed by, or sponsored by Autodesk, Inc. Autodesk and Autodesk Inventor are registered trademarks of Autodesk, Inc.*

---

## Future Directions

### 1. Advanced Geometric Features (Expanding Expressive Power)
* **`RevolveFeature`**: 360° rotational extrusions around axes for axisymmetric components (engine nozzles, shafts, rounded housings, bushings).
* **`Loft` & `Sweep`**: Smooth cross-sectional morphing (e.g., square-to-round aerodynamic ducting) and path-following sweeps for complex tubing/wiring conduits.
* **`Fillet` & `Chamfer`**: Declarative edge-blending operations for automated stress-concentration relief and ergonomic surface finishing.
* **`CircularPattern` & `RectangularPattern`**: High-performance feature replication (e.g., bolt circles, multi-arm drone frames, gear teeth) without manual coordinate trigonometry.

### 2. Native Simulation & FEA Automation
* **Autodesk Inventor `StressAnalysis` / Nastran COM Integration**: Direct COM triggers for automated tetrahedral meshing, boundary constraint application, 3D von Mises stress tensor solving, and headless screenshot rendering of color stress heatmaps.
* **Automated Generative Optimization Loops**: Autonomous CAD -> FEA -> Geometry Reinforcement -> Re-verification loops driven by AI Coding Agents.

### 3. Advanced Multi-Component Assembly Engine
* **Generalized 3D Assembly Constraints**: Declarative `Mate`, `Flush`, `Insert`, and `Tangent` joints with 6-DOF spatial matrix transformations.
* **Automated Clearance & Interference Checking**: Programmatic collision detection between rotating parts (e.g., propeller-to-duct clearance verification).
