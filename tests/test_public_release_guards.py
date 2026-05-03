"""Regression guards for public-repo quality checks."""

from __future__ import annotations

import ast

from conftest import ROOT


def _read_text(relative_path: str) -> str:
    """Read a repository file as UTF-8 text."""
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _parse_module(relative_path: str) -> ast.Module:
    """Parse a Python module from the repository."""
    return ast.parse(_read_text(relative_path))


def _find_function(module: ast.Module, function_name: str) -> ast.FunctionDef:
    """Return the named function from a parsed module."""
    for node in ast.walk(module):
        if isinstance(node, ast.FunctionDef) and node.name == function_name:
            return node
    raise AssertionError(f"Function {function_name!r} was not found")


def _annotation_text(annotation: ast.expr | None) -> str | None:
    """Return a stable string form for an annotation node."""
    if annotation is None:
        return None
    return ast.unparse(annotation)


def test_ci_workflow_installs_and_runs_pyright() -> None:
    """CI should install the dev toolchain and execute pyright explicitly."""
    workflow_text = _read_text(".github/workflows/ci.yml")

    assert 'pip install -e ".[dev]"' in workflow_text
    assert "- name: Pyright" in workflow_text
    assert "run: pyright" in workflow_text


def test_reviewed_helpers_keep_explicit_type_annotations() -> None:
    """Review-follow-up helpers should keep the explicit typing we rely on."""
    other_records_module = _parse_module("src/frontend/ui_dialogs/other_records_dialog.py")
    privacy_module = _parse_module("src/core/privacy.py")

    show_dialog = _find_function(other_records_module, "show_other_records_dialog")
    build_visit_tab = _find_function(other_records_module, "_build_visit_tab")
    build_event_tab = _find_function(other_records_module, "_build_event_tab")
    build_fernet = _find_function(privacy_module, "_build_fernet")

    assert _annotation_text(show_dialog.args.args[0].annotation) == "Tk | Toplevel"
    assert _annotation_text(show_dialog.args.args[1].annotation) == "AppService | None"
    assert _annotation_text(show_dialog.returns) == "None"

    assert _annotation_text(build_visit_tab.args.args[0].annotation) == "ttk.Frame"
    assert _annotation_text(build_visit_tab.args.args[1].annotation) == "AppService"
    assert _annotation_text(build_visit_tab.returns) == "Callable[[], None]"

    assert _annotation_text(build_event_tab.args.args[0].annotation) == "ttk.Frame"
    assert _annotation_text(build_event_tab.args.args[1].annotation) == "AppService"
    assert _annotation_text(build_event_tab.returns) == "Callable[[], None]"

    assert _annotation_text(build_fernet.returns) == "FernetProtocol"
