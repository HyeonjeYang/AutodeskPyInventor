from pathlib import Path

import autodesk_pyinventor as api


# CLI equivalent:
# autodesk-pyinventor washer --od 80 --id 25 --thickness 8 --output C:\temp\washer.ipt

app = api.connect(visible=True)
part = api.Part.new(app=app, name="washer", path=Path(r"C:\temp\washer.ipt"))

part.washer(od=80, id=25, thickness=8)
part.save()
part.close()
