from pathlib import Path

import autodesk_pyinventor as api


app = api.connect(visible=True)
part = api.Part.new(app=app, name="disk_with_hole", path=Path(r"C:\temp\disk_with_hole.ipt"))

part.disk(od=80, id=25, thickness=8)
part.save()
part.export_stl(Path(r"C:\temp\disk_with_hole.stl"))
part.close()
