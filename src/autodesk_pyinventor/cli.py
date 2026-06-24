"""Command-line interface."""

from __future__ import annotations

import argparse
import os
import platform
import sys
import tempfile
from importlib import import_module
from pathlib import Path
from typing import Any, Sequence, cast

from .app import connect
from .constants import WINDOWS_OS_NAME
from .documents import find_standard_part_template
from .exceptions import AutodeskPyInventorError
from .part import Part
from .plan import FeaturePlan
from .recipes import disk_plan, flanged_tube_plan, tube_plan, washer_plan


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autodesk-pyinventor",
        description="Generate simple Autodesk Inventor parts from safe feature plans.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Check local Autodesk Inventor readiness.")
    doctor.add_argument(
        "--strict",
        action="store_true",
        help="Return exit code 1 when any readiness check fails.",
    )

    disk = subparsers.add_parser("disk", help="Generate a disk, optionally with a center bore.")
    _add_common_args(disk)
    disk.add_argument("--od", type=float, required=True)
    disk.add_argument("--id", dest="inner_diameter", type=float, default=0)
    disk.add_argument("--thickness", type=float, default=1)

    washer = subparsers.add_parser("washer", help="Generate a washer.")
    _add_common_args(washer)
    washer.add_argument("--od", type=float, required=True)
    washer.add_argument("--id", dest="inner_diameter", type=float, required=True)
    washer.add_argument("--thickness", type=float, required=True)

    tube = subparsers.add_parser("tube", help="Generate a straight tube.")
    _add_common_args(tube)
    tube.add_argument("--od", type=float, required=True)
    tube.add_argument("--id", dest="inner_diameter", type=float, required=True)
    tube.add_argument("--length", type=float, required=True)

    flanged = subparsers.add_parser("flanged-tube", help="Generate a tube with one flange.")
    _add_common_args(flanged)
    flanged.add_argument("--body-od", type=float, required=True)
    flanged.add_argument("--body-id", type=float, required=True)
    flanged.add_argument("--body-length", type=float, required=True)
    flanged.add_argument("--flange-od", type=float, required=True)
    flanged.add_argument("--flange-thickness", type=float, required=True)
    flanged.add_argument("--flange-z", type=float, default=0)

    return parser


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--name", default=None)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--template", type=Path)
    parser.add_argument("--stl", type=Path)
    parser.add_argument("--visible", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print dry-run output as JSON.")


def plan_from_args(args: argparse.Namespace) -> FeaturePlan:
    name = _plan_name(args)
    if args.command == "disk":
        return disk_plan(
            name=name,
            od=args.od,
            id=args.inner_diameter,
            thickness=args.thickness,
        )
    if args.command == "washer":
        return washer_plan(
            name=name,
            od=args.od,
            id=args.inner_diameter,
            thickness=args.thickness,
        )
    if args.command == "tube":
        return tube_plan(name=name, od=args.od, id=args.inner_diameter, length=args.length)
    if args.command == "flanged-tube":
        return flanged_tube_plan(
            name=name,
            body_od=args.body_od,
            body_id=args.body_id,
            body_length=args.body_length,
            flange_od=args.flange_od,
            flange_thickness=args.flange_thickness,
            flange_z=args.flange_z,
        )
    raise ValueError(f"unsupported command: {args.command}")


def _plan_name(args: argparse.Namespace) -> str:
    if args.name:
        return str(args.name)
    output = getattr(args, "output", None)
    if output is not None:
        return Path(output).stem
    if args.command == "disk" and getattr(args, "inner_diameter", 0) > 0:
        return "washer"
    return str(args.command).replace("-", "_")


def run(args: argparse.Namespace) -> int:
    if args.command == "doctor":
        return run_doctor(strict=args.strict)

    plan = plan_from_args(args)

    if args.dry_run:
        if args.json:
            print(plan.to_json())
        else:
            print(
                plan.explain(
                    path=args.output,
                    template=args.template or "standard.ipt",
                )
            )
        return 0

    if args.output is None:
        raise AutodeskPyInventorError("--output is required unless --dry-run is set.")

    app = connect(visible=args.visible)
    part = Part.from_plan(app=app, plan=plan, path=args.output, template=args.template)
    try:
        part.save()
        if args.stl is not None:
            part.export_stl(args.stl)
    finally:
        part.close()

    return 0


def run_doctor(*, strict: bool = False) -> int:
    lines = ["AutodeskPyInventor doctor", ""]
    checks: list[bool] = []

    def add_check(label: str, value: str, ok: bool, fix: str | None = None) -> None:
        checks.append(ok)
        lines.append(_status(label, value, ok, fix))

    current_os = platform.platform()
    is_windows = os.name == WINDOWS_OS_NAME
    add_check("OS", current_os, is_windows, "Autodesk Inventor requires Windows.")
    add_check(
        "Python",
        platform.python_version(),
        sys.version_info >= (3, 10),
        "Install Python 3.10 or newer.",
    )

    win32_client: Any | None = None
    pywin32_ok = False
    try:
        win32_client = cast(Any, import_module("win32com.client"))
        pywin32_ok = True
    except ImportError:
        pass
    add_check(
        "pywin32",
        "installed" if pywin32_ok else "missing",
        pywin32_ok,
        "pywin32 is not installed. Run: python -m pip install pywin32",
    )

    app: Any | None = None
    constants: Any | None = None
    if is_windows and win32_client is not None:
        try:
            app = win32_client.gencache.EnsureDispatch("Inventor.Application")
            constants = win32_client.constants
            add_check("Inventor COM", "connected", True)
        except Exception:
            add_check(
                "Inventor COM",
                "failed",
                False,
                "Inventor COM connection failed. Make sure Autodesk Inventor is installed.",
            )
    else:
        add_check(
            "Inventor COM",
            "skipped",
            False,
            "Inventor COM can only be checked on Windows with pywin32 installed.",
        )

    version = _inventor_version(app)
    add_check("Inventor version", version or "unavailable", version is not None)

    constants_ok = constants is not None
    add_check(
        "Constants",
        "loaded" if constants_ok else "unavailable",
        constants_ok,
        "Constants are unavailable. Try clearing the win32com gen_py cache.",
    )

    if app is not None:
        try:
            template = find_standard_part_template(app, constants=constants)
            add_check("Part template", f"found ({template})", True)
        except Exception:
            add_check(
                "Part template",
                "not found",
                False,
                "Template not found. Pass --template C:\\path\\to\\Standard.ipt",
            )
    else:
        add_check(
            "Part template",
            "skipped",
            False,
            "Template lookup requires a working Inventor COM connection.",
        )

    add_check(
        "Writable output directory",
        str(Path.cwd()),
        _cwd_is_writable(),
        "Current directory is not writable. Choose another output directory.",
    )

    print("\n".join(lines))
    return 1 if strict and not all(checks) else 0


def _status(label: str, value: str, ok: bool, fix: str | None = None) -> str:
    suffix = "OK" if ok else "FAIL"
    line = f"{label}: {value} {suffix}"
    if not ok and fix:
        line = f"{line}\n  Fix: {fix}"
    return line


def _inventor_version(app: Any | None) -> str | None:
    if app is None:
        return None
    for attribute in ("SoftwareVersion", "Version"):
        value = getattr(app, attribute, None)
        if value:
            return str(value)
    return None


def _cwd_is_writable() -> bool:
    try:
        with tempfile.NamedTemporaryFile(
            dir=Path.cwd(),
            prefix="autodesk_pyinventor_",
            delete=True,
        ):
            return True
    except OSError:
        return False


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run(args)
    except AutodeskPyInventorError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
