# AutodeskPyInventor

Unofficial Windows-only Python-first automation helpers for Autodesk Inventor.

This project is unofficial and is not affiliated with, endorsed by, or sponsored by Autodesk.

## Requirements

- Windows
- Python 3.10+
- Autodesk Inventor
- pywin32

## Install

```powershell
pip install -e .[dev]
```

## Python API

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

## CLI

```powershell
autodesk-pyinventor washer --od 80 --id 25 --thickness 8 --dry-run
```

Real Inventor execution requires `--output`.

## Development

```powershell
pytest
ruff check .
mypy
```

Integration tests require Autodesk Inventor and are opt-in:

```powershell
$env:AUTODESK_PYINVENTOR_RUN_INTEGRATION=1
pytest tests/integration
```

Commit after each import step.

## License

MIT License. See [LICENSE](LICENSE).
