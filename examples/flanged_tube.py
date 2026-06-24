from pathlib import Path

import autodesk_pyinventor as api


app = api.connect(visible=True)
part = api.Part.new(app=app, name="flanged_tube", path=Path(r"C:\temp\flanged_tube.ipt"))

part.flanged_tube(
    body_od=63.5,
    body_id=56.5,
    body_length=236,
    flange_od=90,
    flange_thickness=8,
    flange_z=0,
)
part.save()
part.close()
