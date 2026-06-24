import autodesk_pyinventor as api


part = api.Part.dry_run(name="flanged_tube")
part.flanged_tube(od=50, id=35, length=120, flange_od=85, flange_thickness=12)

print(part.to_json())
