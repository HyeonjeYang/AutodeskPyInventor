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
- Use `part_doc.SaveAs(stl_path, True)` for STL export.

Assembly placement rule for future work:

```python
tg = app.TransientGeometry
matrix = tg.CreateMatrix()
vec = tg.CreateVector(x_cm, y_cm, z_cm)
matrix.SetTranslation(vec)
```

Do not write translation by assigning matrix cells.
