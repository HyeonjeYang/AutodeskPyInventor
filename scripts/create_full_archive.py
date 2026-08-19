"""Package the demo projects (code, docs, generated CAD/STL) into a ZIP under dist/."""

from pathlib import Path
import zipfile

BASE_DIR = Path(__file__).resolve().parents[1]
DIST_DIR = BASE_DIR / "dist"
OUTPUT_ZIP = DIST_DIR / "autodesk_pyinventor_projects_complete.zip"
PROJECT_DIRS = [
    BASE_DIR / "projects" / "micro_drone_project",
    BASE_DIR / "projects" / "camera_rotator_project",
]


def main() -> None:
    DIST_DIR.mkdir(exist_ok=True)
    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        for project_dir in PROJECT_DIRS:
            if not project_dir.exists():
                continue
            for f in project_dir.rglob("*"):
                if f.is_file() and "__pycache__" not in f.parts:
                    zipf.write(f, arcname=str(f.relative_to(BASE_DIR)))
    print(f"[OK] Created {OUTPUT_ZIP.relative_to(BASE_DIR)} ({OUTPUT_ZIP.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
