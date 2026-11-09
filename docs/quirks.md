# Inventor COM Quirks

Current avoidance rules:

- Use `win32com.client.gencache.EnsureDispatch("Inventor.Application")`.
- Load `win32com.client.constants` after dispatch.
- Fail clearly if required Inventor constants are unavailable.
- Do not use `Documents.Add()` for MVP part creation.
- Find a standard `.ipt` template, copy it to the output path, then open the copy.
- Never save modifications back to the original template.
- Use Inventor collection `.Item(n)` calls.
- Treat Inventor collections as one-indexed.
- Use `WorkPlanes.Item(3)` for XY.
- Do not create a zero-offset work plane.
- Hide nonzero offset work planes.
- Do not rely on annular profile detection from concentric circles.
- Create all outer solids first.
- Apply the central bore once at the end.
- Export STL through the STL translator add-in
  (`{533E9A98-FC3B-11D4-8E7E-0010B541CD80}`, cast to `TranslatorAddIn`) with explicit
  options: `ExportUnits` 5 = mm (4 = cm, 2 = inch), `Resolution` 0/1/2 = high/medium/low.
  `part_doc.SaveAs(stl_path, True)` silently reuses the translator's last saved units.
- Call `Activate()` on the STL translator first: an inactive translator accepts
  `SaveCopyAs` without error but writes no file.
- Gencache (early-bound) wrappers return base interfaces that hide members until
  `win32com.client.CastTo`: `ExtrudeFeature.Extent` → `"DistanceExtent"` (for
  `Distance`), `Documents.Open`/`Documents.Add` → `"PartDocument"` or
  `"AssemblyDocument"` (for `ComponentDefinition`), an add-in → `"TranslatorAddIn"`.
- The default `Standard.ipt` template may be inch-based; set
  `UnitsOfMeasure.LengthUnits = kMillimeterLengthUnits` if the saved part should display mm.
- A hidden Inventor (`Visible = False`) started through COM is not registered for
  `GetActiveObject`, so later connections cannot reuse it, and it keeps running after
  Python exits. Call `app.quit_if_launched()` (the CLI does this unless `--visible`).
- A session found by `GetActiveObject` belongs to the user: never hide or quit it.

Assembly placement rule for future work:

```python
tg = app.TransientGeometry
matrix = tg.CreateMatrix()
vec = tg.CreateVector(x_cm, y_cm, z_cm)
matrix.SetTranslation(vec)
```

Do not write translation by assigning matrix cells.
