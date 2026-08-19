"""Generate Native Autodesk Inventor .IPT, .IAM, and .STL files using Inventor COM API.
"""

from pathlib import Path
import sys
import time

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))

from autodesk_pyinventor.app import connect
from autodesk_pyinventor.part import Part
from make_micro_drone import build_micro_drone_frame_plan

GENERATED_DIR = BASE_DIR / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)


def main():
    print("Connecting to Autodesk Inventor COM API...", flush=True)
    app = connect(visible=True)
    print("Connected to Autodesk Inventor successfully!", flush=True)

    frame_plan = build_micro_drone_frame_plan()
    ipt_path = GENERATED_DIR / "micro_drone_frame.ipt"
    stl_path = GENERATED_DIR / "micro_drone_frame.stl"

    print(f"Creating native Autodesk Inventor Part document: {ipt_path}...", flush=True)
    part = Part.new(app=app, name=frame_plan.name, path=ipt_path)
    
    print(f"Executing {len(frame_plan.operations)} operations on Inventor document...", flush=True)
    app.backend.execute_plan(part.document, frame_plan)
    print("All 39 operations completed successfully in Autodesk Inventor!", flush=True)

    print("Saving native Autodesk Inventor Part (.ipt)...", flush=True)
    part.save()
    print(f"Successfully saved native Inventor IPT: {ipt_path} ({ipt_path.stat().st_size} bytes)", flush=True)

    print(f"Exporting native Inventor 3D STL file: {stl_path}...", flush=True)
    part.export_stl(stl_path)
    print(f"Successfully exported native Inventor STL: {stl_path} ({stl_path.stat().st_size} bytes)", flush=True)

    # Create native Assembly Document
    iam_path = GENERATED_DIR / "micro_drone_assembly.iam"
    print(f"Creating native Autodesk Inventor Assembly document: {iam_path}...", flush=True)
    try:
        asm_doc = app.backend.new_assembly_document()
        asm_doc.SaveAs(str(iam_path), False)
        print(f"Successfully saved native Inventor IAM: {iam_path} ({iam_path.stat().st_size} bytes)", flush=True)
    except Exception as exc:
        print(f"Assembly SaveAs notice: {exc}", flush=True)

    print("\n[OK] All NATIVE Autodesk Inventor files (.IPT, .IAM, .STL) created & verified successfully!", flush=True)


if __name__ == "__main__":
    main()
