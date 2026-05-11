from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

try:
    from evalhub import SyncEvalHubClient
    from evalhub.models import (
        BenchmarkConfig,
        EvaluationExports,
        EvaluationExportsOCI,
        ExperimentConfig,
        ExperimentTag,
        JobSubmissionRequest,
        ModelConfig,
        OCIConnectionConfig,
        OCICoordinates,
    )
except ImportError as exc:
    msg = (
        "This quickstart needs the EvalHub client dependencies. "
        'Run it with `uv run --with "eval-hub-sdk[client]==0.1.5" '
        "python quickstart/submit_evalhub_job.py`."
    )
    raise SystemExit(msg) from exc

from common import (
    build_evalhub_parameters,
    evaluated_model_name,
    evaluated_model_url,
    generated_run_suffix,
    load_quickstart_fixture,
    print_json,
    selected_benchmarks,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = REPO_ROOT / "quickstart" / "fixtures" / "first-line-support.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Submit a Gaussia EvalHub job from a fixture.")
    parser.add_argument(
        "--fixture",
        type=Path,
        default=DEFAULT_FIXTURE,
        help="Fixture containing parameters.dataset and parameters.metadata content.",
    )
    parser.add_argument(
        "--benchmarks",
        default="auto",
        help='Comma-separated benchmark ids or "auto" to select by fixture length.',
    )
    parser.add_argument(
        "--unique-run",
        action="store_true",
        help="Append a generated suffix to session, stream, and control metadata.",
    )
    parser.add_argument(
        "--run-suffix",
        help="Explicit suffix to append to session, stream, and control metadata.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the JobSubmissionRequest without calling EvalHub.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    fixture = load_quickstart_fixture(args.fixture)
    try:
        benchmarks = selected_benchmarks(args.benchmarks, fixture)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    run_suffix = args.run_suffix or (generated_run_suffix() if args.unique_run else None)
    parameters = build_evalhub_parameters(fixture, run_suffix=run_suffix)
    request = build_job_submission_request(
        fixture=fixture,
        parameters=parameters,
        benchmark_ids=benchmarks,
    )

    if args.dry_run:
        print_json(request.model_dump(mode="json", exclude_none=True))
        return

    with build_client_from_env() as client:
        job = client.jobs.submit(request)

    print_json(
        {
            "status": "submitted",
            "job_id": job.id,
            "request_name": request.name,
            "benchmark_ids": benchmarks,
            "session_id": parameters["dataset"]["session_id"],
            "stream_id": parameters["metadata"].get("stream_id", ""),
            "control_id": parameters["metadata"].get("control_id", ""),
        }
    )


def build_client_from_env() -> SyncEvalHubClient:
    return SyncEvalHubClient(
        base_url=os.environ.get("EVALHUB_BASE_URL", "http://localhost:8080"),
        auth_token=os.environ.get("EVALHUB_AUTH_TOKEN"),
        auth_token_path=os.environ.get("EVALHUB_AUTH_TOKEN_PATH"),
        insecure=os.environ.get("EVALHUB_INSECURE", "false").lower() == "true",
        tenant=os.environ.get("EVALHUB_TENANT", "default"),
    )


def build_job_submission_request(
    *,
    fixture: dict[str, Any],
    parameters: dict[str, Any],
    benchmark_ids: list[str],
) -> JobSubmissionRequest:
    metadata = parameters["metadata"]
    return JobSubmissionRequest(
        name=build_request_name(metadata),
        description="Gaussia evaluation for an AI agent conversation",
        tags=["gaussia", "evalhub", "agent-evaluation"],
        model=ModelConfig(
            name=evaluated_model_name(fixture),
            url=evaluated_model_url(fixture),
        ),
        benchmarks=[
            BenchmarkConfig(
                id=benchmark_id,
                provider_id="gaussia",
                parameters=parameters,
            )
            for benchmark_id in benchmark_ids
        ],
        experiment=build_experiment(metadata),
        exports=build_exports(),
    )


def build_request_name(metadata: dict[str, Any]) -> str:
    source = "-".join(
        value
        for value in (
            "gaussia-agent-eval",
            metadata.get("assistant_id", ""),
            metadata.get("session_id", ""),
            metadata.get("control_id", ""),
        )
        if value
    )
    return source.lower().replace("_", "-")[:120].rstrip("-")


def build_experiment(metadata: dict[str, Any]) -> ExperimentConfig:
    return ExperimentConfig(
        name=os.environ.get("EVALHUB_EXPERIMENT_NAME", "gaussia-agent-evaluation"),
        tags=[
            ExperimentTag(key="assistant_id", value=str(metadata.get("assistant_id", ""))),
            ExperimentTag(key="session_id", value=str(metadata.get("session_id", ""))),
            ExperimentTag(key="stream_id", value=str(metadata.get("stream_id", ""))),
            ExperimentTag(key="control_id", value=str(metadata.get("control_id", ""))),
        ],
    )


def build_exports() -> EvaluationExports | None:
    oci_host = os.environ.get("EVALHUB_EXPORT_OCI_HOST")
    oci_repository = os.environ.get("EVALHUB_EXPORT_OCI_REPOSITORY")
    if not oci_host and not oci_repository:
        return None
    if not oci_host or not oci_repository:
        raise ValueError(
            "OCI export requires both EVALHUB_EXPORT_OCI_HOST and EVALHUB_EXPORT_OCI_REPOSITORY"
        )

    coordinates = OCICoordinates(
        oci_host=oci_host,
        oci_repository=oci_repository,
        oci_tag=os.environ.get("EVALHUB_EXPORT_OCI_TAG"),
        oci_subject=os.environ.get("EVALHUB_EXPORT_OCI_SUBJECT"),
        annotations={},
    )
    return EvaluationExports(
        oci=EvaluationExportsOCI(
            coordinates=coordinates,
            k8s=(
                OCIConnectionConfig(connection=os.environ["EVALHUB_EXPORT_OCI_K8S_CONNECTION"])
                if os.environ.get("EVALHUB_EXPORT_OCI_K8S_CONNECTION")
                else None
            ),
        )
    )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
