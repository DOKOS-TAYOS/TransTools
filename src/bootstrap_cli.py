"""CLI entry point for shared bootstrap workflows."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from bootstrap.run_workflow import run_application
from bootstrap.setup_workflow import run_setup
from bootstrap.types import RunOptions, SetupOptions


def _build_parser() -> argparse.ArgumentParser:
    """Build the bootstrap CLI argument parser."""
    parser = argparse.ArgumentParser(description="TransTools bootstrap helper")
    subparsers = parser.add_subparsers(dest="command", required=True)

    setup_parser = subparsers.add_parser("setup", help="Create or refresh the local .venv")
    setup_parser.add_argument(
        "--skip-shortcut",
        action="store_true",
        help="Skip desktop shortcut creation on Windows.",
    )

    run_parser = subparsers.add_parser("run", help="Validate and launch TransTools")
    run_parser.add_argument("--check", action="store_true", help="Only validate the installation.")
    run_parser.add_argument(
        "--console",
        action="store_true",
        help="Force the console interpreter instead of pythonw on Windows.",
    )
    run_parser.add_argument("app_args", nargs=argparse.REMAINDER, help="Arguments for src/main.py.")
    return parser


def main() -> int:
    """Run the requested bootstrap workflow."""
    parser = _build_parser()
    args = parser.parse_args()
    project_root = Path(__file__).resolve().parent.parent

    if args.command == "setup":
        return run_setup(
            SetupOptions(
                project_root=project_root,
                bootstrap_python=Path(sys.executable),
                create_windows_shortcut=not args.skip_shortcut,
            )
        )

    app_args = tuple(argument for argument in args.app_args if argument != "--")
    return run_application(
        RunOptions(
            project_root=project_root,
            args=app_args,
            check_only=args.check,
            force_console=args.console,
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
