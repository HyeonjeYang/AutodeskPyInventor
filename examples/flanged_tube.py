from pathlib import Path

import autodesk_pyinventor as api


app = api.connect(visible=True)
part = api.Part.new(app=app, name="flanged_tube", path=Path(r"C:\temp\flanged_tube.ipt"))

part.flanged_tube(od=50, id=35, length=120, flange_od=85, flange_thickness=12)
part.save()
part.close()
