"""Client for running Makefile targets from the repository root."""

from __future__ import annotations

import subprocess
from collections.abc import Callable
from pathlib import Path


OutputCallback = Callable[[str], None]


class MakeClient:
    """Invoke ``make`` targets with optional live output streaming."""

    def __init__(self, repo_root: Path) -> None:
        self._repo_root = repo_root

    @property
    def repo_root(self) -> Path:
        return self._repo_root

    def run(
        self,
        target: str,
        extra_vars: dict[str, str] | None = None,
        on_output: OutputCallback | None = None,
    ) -> tuple[int, str]:
        cmd = ["make", "-C", str(self._repo_root), target]
        if extra_vars:
            for key, value in extra_vars.items():
                cmd.append(f"{key}={value}")

        cmd_str = " ".join(cmd)
        collected: list[str] = []

        def emit(body: str) -> None:
            if on_output is not None:
                on_output(body)

        emit(f"$ {cmd_str}\n\nRunning…")

        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=str(self._repo_root),
            )
            assert proc.stdout is not None
            for line in iter(proc.stdout.readline, ""):
                collected.append(line)
                emit(f"$ {cmd_str}\n\n{''.join(collected)}")
            proc.wait()
            if not collected:
                collected.append("(no output)\n")
            returncode = proc.returncode
        except FileNotFoundError:
            collected.append(
                "ERROR: 'make' not found. Ensure GNU Make is installed.\n"
            )
            returncode = 1

        full = "".join(collected)
        status = "Done" if returncode == 0 else f"Exit code {returncode}"
        emit(f"$ {cmd_str}\n\n{full}\n\n{status}")
        return returncode, full
