"""Command-line interface."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .app import connect
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

    disk = subparsers.add_parser("disk", help="Generate a disk, optionally with a center bore.")
    _add_common_args(disk)
    disk.add_argument("--od", type=float, required=True)
    disk.add_argument("--id", dest="inner_diameter", type=float)
    disk.add_argument("--thickness", type=float, required=True)

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
    flanged.add_argument("--od", type=float, required=True)
    flanged.add_argument("--id", dest="inner_diameter", type=float, required=True)
    flanged.add_argument("--length", type=float, required=True)
    flanged.add_argument("--flange-od", type=float, required=True)
    flanged.add_argument("--flange-thickness", type=float, required=True)

    return parser


def _add_common_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--name", default=None)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--stl", type=Path)
    parser.add_argument("--visible", action="store_true")
    parser.add_argument("--dry-run", action="store_true")


def plan_from_args(args: argparse.Namespace) -> FeaturePlan:
    name = args.name or args.command.replace("-", "_")
    if args.command == "disk":
        return disk_plan(
            od=args.od,
            id=args.inner_diameter,
            thickness=args.thickness,
            name=name,
        )
    if args.command == "washer":
        return washer_plan(
            od=args.od,
            id=args.inner_diameter,
            thickness=args.thickness,
            name=name,
        )
    if args.command == "tube":
        return tube_plan(od=args.od, id=args.inner_diameter, length=args.length, name=name)
    if args.command == "flanged-tube":
        return flanged_tube_plan(
            od=args.od,
            id=args.inner_diameter,
            length=args.length,
            flange_od=args.flange_od,
            flange_thickness=args.flange_thickness,
            name=name,
        )
    raise ValueError(f"unsupported command: {args.command}")


def run(args: argparse.Namespace) -> int:
    plan = plan_from_args(args)

    if args.dry_run:
        print(plan.to_json())
        return 0

    if args.output is None:
        raise AutodeskPyInventorError("--output is required unless --dry-run is set.")

    app = connect(visible=args.visible)
    part = Part.new(app=app, name=plan.name, path=args.output)
    try:
        part.apply_plan(plan)
        part.save()
        if args.stl is not None:
            part.export_stl(args.stl)
    finally:
        part.close()

    return 0


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
