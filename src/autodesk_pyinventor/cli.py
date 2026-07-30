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
from .assembly import Assembly, EnclosureAssemblyPlan
from .constants import WINDOWS_OS_NAME
from .documents import find_standard_part_template
from .exceptions import AutodeskPyInventorError
from .part import Part
from .plan import EnclosurePlan, FeaturePlan
from .recipes import (
    astro_controller_enclosure_plan,
    disk_plan,
    flanged_tube_plan,
    tube_plan,
    washer_plan,
)


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

    enclosure = subparsers.add_parser(
        "astro-controller-enclosure",
        help="Generate the Astro Controller Base and Lid enclosure parts.",
    )
    enclosure.add_argument("--name", default="astro_controller_enclosure")
    enclosure.add_argument("--base-output", type=Path)
    enclosure.add_argument("--lid-output", type=Path)
    enclosure.add_argument("--base-stl", type=Path)
    enclosure.add_argument("--lid-stl", type=Path)
    enclosure.add_argument("--template", type=Path)
    enclosure.add_argument("--visible", action="store_true")
    enclosure.add_argument("--dry-run", action="store_true")
    enclosure.add_argument("--validate-only", action="store_true")
    enclosure.add_argument("--json", action="store_true", help="Print dry-run output as JSON.")
    enclosure.add_argument("--wall", type=float, default=2.0)
    enclosure.add_argument("--out-x", type=float, default=84.0)
    enclosure.add_argument("--out-y", type=float, default=58.0)
    enclosure.add_argument("--base-h", type=float, default=29.5)
    enclosure.add_argument("--lid-t", type=float, default=3.0)
    enclosure.add_argument("--boss-h", type=float, default=4.0)
    enclosure.add_argument("--fit", type=float, default=0.3)
    enclosure.add_argument("--oled-window-width", type=float, default=23.0)
    enclosure.add_argument("--oled-window-height", type=float, default=12.5)
    enclosure.add_argument("--oled-window-x", type=float, default=28.0)
    enclosure.add_argument("--oled-window-y", type=float, default=35.0)
    enclosure.add_argument("--oled-pocket-size", type=float, default=28.6)
    enclosure.add_argument("--oled-pocket-depth", type=float, default=1.8)
    enclosure.add_argument("--encoder-hole-diameter", type=float, default=7.2)

    assembly = subparsers.add_parser(
        "astro-controller-assembly",
        help="Place Astro Controller Base and Lid parts in an Inventor assembly.",
    )
    assembly.add_argument("--name", default="astro_controller")
    assembly.add_argument("--base-input", type=Path)
    assembly.add_argument("--lid-input", type=Path)
    assembly.add_argument("--output", type=Path)
    assembly.add_argument("--base-h", type=float, default=29.5)
    assembly.add_argument("--visible", action="store_true")
    assembly.add_argument("--dry-run", action="store_true")
    assembly.add_argument("--validate-only", action="store_true")
    assembly.add_argument("--json", action="store_true")

    return parser


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--name", default=None)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--template", type=Path)
    parser.add_argument("--stl", type=Path)
    parser.add_argument("--visible", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print dry-run output as JSON.")


def plan_from_args(
    args: argparse.Namespace,
) -> FeaturePlan | EnclosurePlan | EnclosureAssemblyPlan:
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
    if args.command == "astro-controller-enclosure":
        return astro_controller_enclosure_plan(
            name=name,
            wall=args.wall,
            out_x=args.out_x,
            out_y=args.out_y,
            base_h=args.base_h,
            lid_t=args.lid_t,
            boss_h=args.boss_h,
            fit=args.fit,
            oled_window_width=args.oled_window_width,
            oled_window_height=args.oled_window_height,
            oled_window_x=args.oled_window_x,
            oled_window_y=args.oled_window_y,
            oled_pocket_size=args.oled_pocket_size,
            oled_pocket_depth=args.oled_pocket_depth,
            encoder_hole_diameter=args.encoder_hole_diameter,
        )
    if args.command == "astro-controller-assembly":
        return EnclosureAssemblyPlan(
            name=name,
            base_input=args.base_input,
            lid_input=args.lid_input,
            output=args.output,
            base_h_mm=args.base_h,
        )
    raise ValueError(f"unsupported command: {args.command}")


def _plan_name(args: argparse.Namespace) -> str:
    if args.name:
        return str(args.name)
    if args.command in ("astro-controller-enclosure", "astro-controller-assembly"):
        return "astro_controller_enclosure"
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

    if args.dry_run or getattr(args, "validate_only", False):
        if args.json:
            print(plan.to_json())
        elif getattr(args, "validate_only", False):
            print(f"valid: {plan.name}")
        else:
            if isinstance(plan, EnclosurePlan):
                print(plan.explain())
            elif isinstance(plan, EnclosureAssemblyPlan):
                print(plan.to_json())
            else:
                print(
                    plan.explain(
                        path=args.output,
                        template=args.template or "standard.ipt",
                    )
                )
        return 0

    if isinstance(plan, EnclosureAssemblyPlan):
        plan.validate_for_execution()
        assembly = Assembly.from_plan(app=connect(visible=args.visible), plan=plan)
        assembly.close()
        return 0

    if isinstance(plan, EnclosurePlan):
        return _run_enclosure(args, plan)

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


def _run_enclosure(args: argparse.Namespace, plan: EnclosurePlan) -> int:
    if args.base_output is None or args.lid_output is None:
        raise AutodeskPyInventorError(
            "--base-output and --lid-output are required unless --dry-run is set."
        )

    app = connect(visible=args.visible)
    parts: list[Part] = []
    documents = [
        (plan.base, args.base_output, args.base_stl),
        (plan.lid, args.lid_output, args.lid_stl),
    ]
    try:
        for document_plan, output, stl in documents:
            part = Part.new(
                app=app,
                name=document_plan.name,
                path=output,
                template=args.template,
            )
            parts.append(part)
            part.execute(document_plan)
            part.save()
            if stl is not None:
                part.export_stl(stl)
    finally:
        for part in reversed(parts):
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
