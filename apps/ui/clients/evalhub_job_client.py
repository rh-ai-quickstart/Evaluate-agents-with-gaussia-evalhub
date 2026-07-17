"""EvalHub API client for submitting and inspecting evaluation jobs."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from config import JOB_SUBMISSION_DIR, REPO_ROOT


def _ensure_job_submission_on_path() -> None:
    path = str(JOB_SUBMISSION_DIR)
    if path not in sys.path:
        sys.path.insert(0, path)


class EvalHubJobClient:
    """Thin wrapper around the shared ``submit_evalhub_job`` library and SDK."""

    def __init__(self, fixtures_dir: Path) -> None:
        self._fixtures_dir = fixtures_dir
        _ensure_job_submission_on_path()

    def submit(
        self,
        *,
        fixture: str,
        benchmarks: str = "auto",
        unique_run: bool = True,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        from submit_evalhub_job import submit_job

        fixture_path = self._fixtures_dir / f"{fixture}.json"
        return submit_job(
            fixture_path=fixture_path,
            benchmarks=benchmarks,
            unique_run=unique_run,
            dry_run=dry_run,
            load_dotenv=True,
        )

    def list_jobs(self, *, limit: int = 25) -> list[dict[str, Any]]:
        from submit_evalhub_job import build_client_from_env
        from common import load_env_files

        load_env_files(REPO_ROOT / ".env", JOB_SUBMISSION_DIR / ".env")
        with build_client_from_env() as client:
            jobs = client.jobs.list(limit=limit)
        return [self._job_summary(job) for job in jobs]

    def get_job(self, job_id: str) -> dict[str, Any]:
        from submit_evalhub_job import build_client_from_env
        from common import load_env_files

        load_env_files(REPO_ROOT / ".env", JOB_SUBMISSION_DIR / ".env")
        with build_client_from_env() as client:
            job = client.jobs.get(job_id)
        return job.model_dump(mode="json", exclude_none=True)

    @staticmethod
    def _job_summary(job: Any) -> dict[str, Any]:
        status = getattr(job, "status", None)
        state_obj = getattr(status, "state", None) if status is not None else None
        if state_obj is None:
            state: Any = None
        else:
            state = getattr(state_obj, "value", None) or str(state_obj)
        created_at = getattr(getattr(job, "resource", None), "created_at", None)
        return {
            "job_id": job.id,
            "name": job.name,
            "status": state,
            "created_at": str(created_at) if created_at is not None else None,
        }
