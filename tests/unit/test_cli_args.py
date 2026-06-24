from __future__ import annotations

import json

import pytest

from autodesk_pyinventor.cli import build_parser, main, plan_from_args


def test_cli_builds_washer_plan_from_disk_with_inner_diameter() -> None:
    parser = build_parser()
    args = parser.parse_args(["disk", "--od", "80", "--id", "25", "--thickness", "8"])

    plan = plan_from_args(args)

    assert plan.name == "washer"
    assert [operation.to_dict()["type"] for operation in plan.operations] == [
        "outer_cylinder",
        "deferred_center_bore",
        "apply_deferred_bores",
    ]


def test_cli_dry_run_prints_human_plan(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            "disk",
            "--output",
            r"C:\temp\washer.ipt",
            "--od",
            "80",
            "--id",
            "25",
            "--thickness",
            "8",
            "--dry-run",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "FeaturePlan: washer" in captured.out
    assert 'apply_center_bore_once(diameter=25, extent="through_all_symmetric")' in captured.out


def test_cli_dry_run_json_shape(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        ["disk", "--od", "80", "--id", "25", "--thickness", "8", "--dry-run", "--json"]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload == {
        "name": "washer",
        "units": "mm",
        "operations": [
            {"type": "outer_cylinder", "diameter": 80, "z": 0, "length": 8},
            {"type": "deferred_center_bore", "diameter": 25, "axis": "Z"},
            {"type": "apply_deferred_bores"},
        ],
    }


def test_cli_flanged_tube_dry_run_defers_bore_once(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(
        [
            "flanged-tube",
            "--body-od",
            "63.5",
            "--body-id",
            "56.5",
            "--body-length",
            "236",
            "--flange-od",
            "90",
            "--flange-thickness",
            "8",
            "--flange-z",
            "0",
            "--dry-run",
        ]
    )

    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.out.count("defer_bore") == 1
    assert captured.out.count("apply_center_bore_once") == 1


def test_cli_requires_output_for_real_execution(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["disk", "--od", "80", "--thickness", "8"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "--output is required" in captured.err


def test_cli_doctor_prints_diagnostics(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["doctor"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "AutodeskPyInventor doctor" in captured.out
    assert "Python:" in captured.out
