from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

try:
    from evalhub.adapter import (
        JobCallbacks,
        JobResults,
        JobSpec,
        JobStatusUpdate,
        OCIArtifactResult,
    )
    from gaussia.integrations.evalhub.adapter import GaussiaEvalHubAdapter
except ImportError as exc:
    msg = (
        "This quickstart needs the Gaussia EvalHub provider dependencies. "
        'Run it with `uv run --with "gaussia[evalhub]" '
        "python quickstart/local_provider_smoke.py`."
    )
    raise SystemExit(msg) from exc

from common import (
    build_evalhub_parameters,
    evaluated_model_name,
    evaluated_model_url,
    load_quickstart_fixture,
    print_json,
    selected_benchmarks,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURE = REPO_ROOT / "quickstart" / "fixtures" / "agent_transcript_long.json"


class ConsoleCallbacks(JobCallbacks):
    def report_status(self, update: JobStatusUpdate) -> None:
        phase = getattr(update.phase, "value", update.phase)
        status = getattr(update.status, "value", update.status)
        message = update.message.message if update.message else ""
        print(f"[status] {status}/{phase}: {message}")

    def create_oci_artifact(self, spec: Any) -> OCIArtifactResult:
        print(f"[artifact] would persist OCI artifact from {spec.files_path}")
        return OCIArtifactResult(
            digest="sha256:local-smoke",
            reference="local/gaussia-evalhub-smoke:latest@sha256:local-smoke",
        )

    def report_results(self, results: JobResults) -> None:
        print_json(results.model_dump(mode="json"))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Gaussia EvalHub adapter locally with a quickstart fixture."
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        default=DEFAULT_FIXTURE,
        help="Fixture containing parameters.dataset and parameters.metadata content.",
    )
    parser.add_argument(
        "--benchmarks",
        default="humanity",
        help='Comma-separated benchmark ids or "auto" to select by fixture length.',
    )
    parser.add_argument(
        "--with-oci",
        action="store_true",
        help="Exercise the adapter OCI artifact callback with a local fake result.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    fixture = load_quickstart_fixture(args.fixture)
    try:
        benchmarks = selected_benchmarks(args.benchmarks, fixture)
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc

    adapter = object.__new__(GaussiaEvalHubAdapter)
    callbacks = ConsoleCallbacks()
    parameters = build_evalhub_parameters(fixture)

    print_json(
        {
            "fixture": str(args.fixture),
            "benchmarks": benchmarks,
            "interactions": len(parameters["dataset"].get("conversation", [])),
            "model_name": evaluated_model_name(fixture),
            "payload": "dataset",
        }
    )

    for index, benchmark_id in enumerate(benchmarks):
        job_spec = build_job_spec(
            fixture=fixture,
            parameters=parameters,
            benchmark_id=benchmark_id,
            benchmark_index=index,
            with_oci=args.with_oci,
        )
        results = adapter.run_benchmark_job(job_spec, callbacks)
        callbacks.report_results(results)


def build_job_spec(
    *,
    fixture: dict[str, Any],
    parameters: dict[str, Any],
    benchmark_id: str,
    benchmark_index: int,
    with_oci: bool,
) -> JobSpec:
    data: dict[str, Any] = {
        "id": f"quickstart-{parameters['metadata'].get('control_id', 'local')}-{benchmark_id}",
        "provider_id": "gaussia",
        "benchmark_id": benchmark_id,
        "benchmark_index": benchmark_index,
        "model": {
            "name": evaluated_model_name(fixture),
            "url": evaluated_model_url(fixture),
        },
        "parameters": parameters,
        "callback_url": "http://localhost:8080/callbacks",
    }
    if with_oci:
        data["exports"] = {
            "oci": {
                "coordinates": {
                    "oci_host": "local",
                    "oci_repository": "gaussia/evalhub-smoke",
                    "oci_tag": benchmark_id,
                    "annotations": {},
                }
            }
        }
    return JobSpec.model_validate(data)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
