"""Regression tests for Windows-friendly atomic save retries."""

from __future__ import annotations

from pathlib import Path

from core import repository


def test_replace_file_with_retry_retries_transient_permission_errors() -> None:
    """Transient file locks should be retried before the save fails."""
    sleep_calls: list[float] = []
    replace_attempts = 0
    replace_calls: list[tuple[Path | str, Path | str]] = []

    def flaky_replace(source: Path | str, destination: Path | str) -> None:
        nonlocal replace_attempts
        replace_attempts += 1
        replace_calls.append((source, destination))
        if replace_attempts == 1:
            raise PermissionError("temporarily locked")

    repository._replace_file_with_retry(
        Path("state.tmp"),
        Path("state.json"),
        replace_func=flaky_replace,
        sleep_func=lambda seconds: sleep_calls.append(seconds),
    )

    assert replace_attempts == 2
    assert replace_calls == [
        (Path("state.tmp"), Path("state.json")),
        (Path("state.tmp"), Path("state.json")),
    ]
    assert sleep_calls == [repository.ATOMIC_SAVE_RETRY_SECONDS]
