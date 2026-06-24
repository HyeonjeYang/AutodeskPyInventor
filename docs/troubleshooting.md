# Troubleshooting

## `pywin32 is required`

Install the package on Windows with:

```powershell
pip install -e .
```

## `Could not start or connect to Autodesk Inventor through COM`

Check that Autodesk Inventor is installed and can be started normally.

## CLI dry run works but real execution fails

Dry run only validates the feature plan. Real execution also needs Windows, pywin32, and Autodesk Inventor.

## Integration tests are skipped

Set the opt-in environment variable:

```powershell
$env:AUTODESK_PYINVENTOR_RUN_INTEGRATION=1
pytest tests/integration
```
