import autodesk_pyinventor as api


part = api.Part.dry_run(name="flanged_tube")
part.flanged_tube(
    body_od=63.5,
    body_id=56.5,
    body_length=236,
    flange_od=90,
    flange_thickness=8,
    flange_z=0,
)

print(part.explain())
