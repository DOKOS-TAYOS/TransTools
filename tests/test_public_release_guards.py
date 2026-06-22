"""Regression guards for public-repo quality checks."""

from __future__ import annotations

import ast
import re
import tomllib

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


def _requirement_name(requirement: str) -> str:
    """Extract the distribution name from a PEP 508-style requirement string."""
    match = re.match(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)", requirement)
    if match is None:
        raise AssertionError(f"Could not parse requirement name from {requirement!r}")
    return match.group(1)


def test_ci_workflow_installs_and_runs_pyright() -> None:
    """CI should install the dev toolchain and execute pyright explicitly."""
    workflow_text = _read_text(".github/workflows/ci.yml")

    assert 'pip install -e ".[dev]"' in workflow_text
    assert "- name: Pyright" in workflow_text
    assert "run: pyright" in workflow_text


def test_ci_workflow_runs_dependency_audit() -> None:
    """CI should fail when installed Python dependencies have known vulnerabilities."""
    workflow_text = _read_text(".github/workflows/ci.yml")

    assert "- name: Pip audit" in workflow_text
    assert "run: pip-audit" in workflow_text


def test_dev_dependencies_include_security_auditor() -> None:
    """The local/CI dev extra should install the dependency-audit command."""
    pyproject_data = tomllib.loads(_read_text("pyproject.toml"))

    dev_dependencies = pyproject_data["project"]["optional-dependencies"]["dev"]

    dependency_names = {_requirement_name(dependency) for dependency in dev_dependencies}

    assert "pip-audit" in dependency_names


def test_dependabot_configuration_covers_project_ecosystems() -> None:
    """Dependabot should watch Python dependencies, docs dependencies, and Actions."""
    config_text = _read_text(".github/dependabot.yml")

    assert 'package-ecosystem: "pip"' in config_text
    assert 'directory: "/"' in config_text
    assert 'directory: "/docs"' in config_text
    assert 'package-ecosystem: "github-actions"' in config_text
    assert 'interval: "weekly"' in config_text


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
