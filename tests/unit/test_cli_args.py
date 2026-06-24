from __future__ import annotations

import json

import pytest

from autodesk_pyinventor.cli import build_parser, main, plan_from_args


def test_cli_builds_washer_plan() -> None:
    parser = build_parser()
    args = parser.parse_args(
        ["washer", "--od", "80", "--id", "25", "--thickness", "8", "--name", "washer"]
    )

    plan = plan_from_args(args)

    assert plan.name == "washer"
    assert [step.action for step in plan.steps] == ["base_cylinder", "center_bore"]


def test_cli_dry_run_prints_json(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["tube", "--od", "50", "--id", "35", "--length", "120", "--dry-run"])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["metadata"]["recipe"] == "tube"


def test_cli_requires_output_for_real_execution(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = main(["disk", "--od", "80", "--thickness", "8"])

    captured = capsys.readouterr()
    assert exit_code == 2
    assert "--output is required" in captured.err
