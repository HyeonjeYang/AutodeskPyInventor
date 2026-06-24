# Troubleshooting

## Start with doctor

```powershell
autodesk-pyinventor doctor
```

It checks OS, Python, pywin32, Inventor COM, constants, part template discovery, and current directory
writability.

Use strict mode in automation:

```powershell
autodesk-pyinventor doctor --strict
```

## `pywin32 is not installed`

Run:

```powershell
python -m pip install pywin32
```

## `Inventor COM connection failed`

Make sure Autodesk Inventor is installed and starts normally.

## `Constants are unavailable`

Try clearing the `win32com` `gen_py` cache, then run `autodesk-pyinventor doctor` again.

## `Template not found`

Pass a template explicitly:

```powershell
autodesk-pyinventor disk --template C:\path\to\Standard.ipt --output C:\temp\disk.ipt --od 80
```

## CLI dry run works but real execution fails

Dry run only validates the feature plan. Real execution also needs Windows, pywin32, Autodesk
Inventor, a writable output directory, and a part template.

## Integration tests are skipped

Set the opt-in environment variable:

```powershell
$env:AUTODESK_PYINVENTOR_RUN_INTEGRATION=1
pytest tests/integration
```
