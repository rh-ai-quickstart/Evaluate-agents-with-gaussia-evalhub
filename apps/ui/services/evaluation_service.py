"""Orchestrate evaluation and cluster make targets for the UI."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from clients.make_client import MakeClient, OutputCallback


class EvaluationService:
    """Map UI actions to Makefile targets via ``MakeClient``."""

    def __init__(self, make_client: MakeClient) -> None:
        self._make = make_client

    @staticmethod
    def generate_run_name() -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"gaussia-evalhub-run-{ts}"

    def submit_run(
        self,
        *,
        humanity_only: bool,
        namespace: str,
        release: str,
        fixture: str,
        run_name: str,
        cpu_request: str,
        memory_request: str,
        cpu_limit: str,
        memory_limit: str,
        on_output: OutputCallback | None = None,
    ) -> tuple[int, str]:
        target = "run-humanity" if humanity_only else "run-all"
        return self._make.run(
            target,
            {
                "NAMESPACE": namespace,
                "RELEASE": release,
                "FIXTURE": fixture,
                "RUN_NAME": run_name,
                "JOB_CPU_REQUEST": cpu_request,
                "JOB_MEMORY_REQUEST": memory_request,
                "JOB_CPU_LIMIT": cpu_limit,
                "JOB_MEMORY_LIMIT": memory_limit,
            },
            on_output=on_output,
        )

    def run_external(
        self,
        *,
        namespace: str,
        release: str,
        fixture: str,
        run_name: str,
        cpu_request: str,
        memory_request: str,
        cpu_limit: str,
        memory_limit: str,
        on_output: OutputCallback | None = None,
    ) -> tuple[int, str]:
        return self._make.run(
            "install-external",
            {
                "NAMESPACE": namespace,
                "RELEASE": release,
                "FIXTURE": fixture,
                "RUN_NAME": run_name,
                "JOB_CPU_REQUEST": cpu_request,
                "JOB_MEMORY_REQUEST": memory_request,
                "JOB_CPU_LIMIT": cpu_limit,
                "JOB_MEMORY_LIMIT": memory_limit,
            },
            on_output=on_output,
        )

    def run_local(
        self,
        *,
        fixture: str,
        on_output: OutputCallback | None = None,
    ) -> tuple[int, str]:
        return self._make.run(
            "run-local",
            {"FIXTURE": fixture},
            on_output=on_output,
        )

    def validate(
        self,
        *,
        namespace: str,
        release: str,
        on_output: OutputCallback | None = None,
    ) -> tuple[int, str]:
        return self._make.run(
            "validate",
            {"NAMESPACE": namespace, "RELEASE": release},
            on_output=on_output,
        )

    def list_releases(
        self,
        *,
        namespace: str,
        release: str,
        on_output: OutputCallback | None = None,
    ) -> tuple[int, str]:
        return self._make.run(
            "list-releases",
            {"NAMESPACE": namespace, "RELEASE": release},
            on_output=on_output,
        )

    def follow_logs(
        self,
        *,
        namespace: str,
        run_name: str,
        on_output: OutputCallback | None = None,
    ) -> tuple[int, str]:
        return self._make.run(
            "logs",
            {"NAMESPACE": namespace, "RUN_NAME": run_name},
            on_output=on_output,
        )

    def wait_for_run(
        self,
        *,
        namespace: str,
        run_name: str,
        on_output: OutputCallback | None = None,
    ) -> tuple[int, str]:
        return self._make.run(
            "wait-run",
            {"NAMESPACE": namespace, "RUN_NAME": run_name},
            on_output=on_output,
        )

    def uninstall_run(
        self,
        *,
        namespace: str,
        run_name: str,
        on_output: OutputCallback | None = None,
    ) -> tuple[int, str]:
        return self._make.run(
            "uninstall-run",
            {"NAMESPACE": namespace, "RUN_NAME": run_name},
            on_output=on_output,
        )
