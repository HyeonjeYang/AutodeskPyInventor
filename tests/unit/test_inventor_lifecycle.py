from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from autodesk_pyinventor import backend as backend_module
from autodesk_pyinventor import cli
from autodesk_pyinventor.app import InventorApp
from autodesk_pyinventor.backend import InventorBackend


class _FakeInventor:
    def __init__(self) -> None:
        self.quit_calls = 0

    def Quit(self) -> None:  # noqa: N802 - COM name
        self.quit_calls += 1


def _app(*, launched: bool) -> tuple[InventorApp, _FakeInventor]:
    raw = _FakeInventor()
    backend = InventorBackend(app=raw, constants=SimpleNamespace(), launched=launched)
    return InventorApp(backend=backend), raw


def test_quit_if_launched_only_quits_instances_this_connection_started() -> None:
    launched_app, launched_raw = _app(launched=True)
    reused_app, reused_raw = _app(launched=False)

    assert launched_app.quit_if_launched() is True
    assert launched_app.quit_if_launched() is False  # already quit
    assert reused_app.quit_if_launched() is False
    assert (launched_raw.quit_calls, reused_raw.quit_calls) == (1, 0)


def _fake_win32(running: SimpleNamespace | None, launched: SimpleNamespace) -> Any:
    def get_active_object(prog_id: str) -> SimpleNamespace:
        if running is None:
            raise OSError("Operation unavailable")
        return running

    client = SimpleNamespace(
        GetActiveObject=get_active_object,
        gencache=SimpleNamespace(EnsureDispatch=lambda prog_id: launched),
        constants=SimpleNamespace(),
    )
    modules = {"pythoncom": SimpleNamespace(CoInitialize=lambda: None), "win32com.client": client}
    return modules.__getitem__


def test_connect_hidden_never_hides_a_reused_user_session(monkeypatch: pytest.MonkeyPatch) -> None:
    user_session = SimpleNamespace(Visible=True)
    monkeypatch.setattr(backend_module.os, "name", "nt")
    monkeypatch.setattr(
        backend_module, "import_module", _fake_win32(user_session, SimpleNamespace())
    )

    backend = InventorBackend.connect(visible=False)

    assert backend.app is user_session
    assert backend.launched is False
    assert user_session.Visible is True


def test_connect_hides_and_marks_an_instance_it_launched(monkeypatch: pytest.MonkeyPatch) -> None:
    new_instance = SimpleNamespace(Visible=True)
    monkeypatch.setattr(backend_module.os, "name", "nt")
    monkeypatch.setattr(backend_module, "import_module", _fake_win32(None, new_instance))

    backend = InventorBackend.connect(visible=False)

    assert backend.app is new_instance
    assert backend.launched is True
    assert new_instance.Visible is False


@pytest.mark.parametrize(
    ("visible", "launched", "expected_quits"),
    [(False, True, 1), (False, False, 0), (True, True, 0)],
)
def test_cli_session_quits_only_a_hidden_instance_it_launched(
    monkeypatch: pytest.MonkeyPatch, visible: bool, launched: bool, expected_quits: int
) -> None:
    app, raw = _app(launched=launched)
    monkeypatch.setattr(cli, "connect", lambda *, visible: app)

    with pytest.raises(RuntimeError):
        with cli._inventor_session(visible=visible):
            raise RuntimeError("build failed")

    assert raw.quit_calls == expected_quits
