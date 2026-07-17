"""Orchestrate EvalHub evaluation submissions for the UI."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from clients.evalhub_job_client import EvalHubJobClient


class EvaluationService:
    """Map UI actions to EvalHub API calls via ``EvalHubJobClient``."""

    def __init__(self, job_client: EvalHubJobClient) -> None:
        self._jobs = job_client

    def submit_run(
        self,
        *,
        humanity_only: bool,
        fixture: str,
        unique_run: bool = True,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        benchmarks = "humanity" if humanity_only else "auto"
        return self._jobs.submit(
            fixture=fixture,
            benchmarks=benchmarks,
            unique_run=unique_run,
            dry_run=dry_run,
        )

    def list_jobs(self, *, limit: int = 25) -> list[dict[str, Any]]:
        return self._jobs.list_jobs(limit=limit)

    def get_job(self, job_id: str) -> dict[str, Any]:
        return self._jobs.get_job(job_id)
