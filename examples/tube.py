from pathlib import Path

import autodesk_pyinventor as api


app = api.connect(visible=True)
part = api.Part.new(app=app, name="tube", path=Path(r"C:\temp\tube.ipt"))

part.tube(od=50, id=35, length=120)
part.save()
part.close()
