from __future__ import annotations

import copy
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ALWAYS_ENABLED_BENCHMARKS = ("humanity", "context", "conversational")
LONG_SESSION_BENCHMARKS = ("bias", "toxicity")
SUPPORTED_BENCHMARKS = (*ALWAYS_ENABLED_BENCHMARKS, *LONG_SESSION_BENCHMARKS)


def main() -> None:
    mode = os.environ.get("QUICKSTART_MODE", "smoke")
    fixture = load_fixture(os.environ["QUICKSTART_FIXTURE_PATH"])
    benchmarks = select_benchmarks(os.environ.get("QUICKSTART_BENCHMARKS", "humanity"), fixture)

    if mode == "smoke":
        run_smoke(fixture, benchmarks)
        return
    if mode == "submit":
        submit_evalhub_job(fixture, benchmarks)
        return
    raise SystemExit(f"Unsupported QUICKSTART_MODE: {mode}")


def run_smoke(fixture: dict[str, Any], benchmarks: list[str]) -> None:
    from evalhub.adapter import JobCallbacks, JobResults, JobSpec, JobStatusUpdate, OCIArtifactResult
    from gaussia.integrations.evalhub.adapter import GaussiaEvalHubAdapter

    class ConsoleCallbacks(JobCallbacks):
        def report_status(self, update: JobStatusUpdate) -> None:
            phase = getattr(update.phase, "value", update.phase)
            status = getattr(update.status, "value", update.status)
            message = update.message.message if update.message else ""
            print(f"[status] {status}/{phase}: {message}")

        def create_oci_artifact(self, spec: Any) -> OCIArtifactResult:
            print(f"[artifact] would persist OCI artifact from {spec.files_path}")
            return OCIArtifactResult(
                digest="sha256:openshift-smoke",
                reference="local/gaussia-evalhub-smoke:latest@sha256:openshift-smoke",
            )

        def report_results(self, results: JobResults) -> None:
            print_json(results.model_dump(mode="json"))

    adapter = object.__new__(GaussiaEvalHubAdapter)
    callbacks = ConsoleCallbacks()
    parameters = build_parameters(fixture)
    print_json(
        {
            "mode": "smoke",
            "benchmarks": benchmarks,
            "interactions": len(parameters["dataset"].get("conversation", [])),
            "model_name": model_name(fixture),
        }
    )

    for index, benchmark_id in enumerate(benchmarks):
        spec = JobSpec.model_validate(
            {
                "id": f"quickstart-{parameters['metadata'].get('control_id', 'openshift')}-{benchmark_id}",
                "provider_id": "gaussia",
                "benchmark_id": benchmark_id,
                "benchmark_index": index,
                "model": {
                    "name": model_name(fixture),
                    "url": model_url(fixture),
                },
                "parameters": parameters,
                "callback_url": "http://localhost:8080/callbacks",
            }
        )
        callbacks.report_results(adapter.run_benchmark_job(spec, callbacks))


def submit_evalhub_job(fixture: dict[str, Any], benchmarks: list[str]) -> None:
    from evalhub import SyncEvalHubClient
    from evalhub.models import (
        BenchmarkConfig,
        ExperimentConfig,
        ExperimentTag,
        JobSubmissionRequest,
        ModelConfig,
    )

    suffix = os.environ.get("QUICKSTART_RUN_SUFFIX")
    if os.environ.get("QUICKSTART_UNIQUE_RUN", "false").lower() == "true" and not suffix:
        suffix = datetime.now(tz=UTC).strftime("%Y%m%d%H%M%S")
    parameters = build_parameters(fixture, run_suffix=suffix)
    metadata = parameters["metadata"]
    request = JobSubmissionRequest(
        name=request_name(metadata),
        description="Gaussia evaluation for an AI agent transcript",
        tags=["gaussia", "evalhub", "agent-evaluation"],
        model=ModelConfig(name=model_name(fixture), url=model_url(fixture)),
        benchmarks=[
            BenchmarkConfig(id=benchmark, provider_id="gaussia", parameters=parameters)
            for benchmark in benchmarks
        ],
        experiment=ExperimentConfig(
            name=os.environ.get("EVALHUB_EXPERIMENT_NAME", "gaussia-agent-evaluation"),
            tags=[
                ExperimentTag(key="assistant_id", value=str(metadata.get("assistant_id", ""))),
                ExperimentTag(key="session_id", value=str(metadata.get("session_id", ""))),
                ExperimentTag(key="stream_id", value=str(metadata.get("stream_id", ""))),
                ExperimentTag(key="control_id", value=str(metadata.get("control_id", ""))),
                ExperimentTag(key="source", value=str(metadata.get("source", ""))),
            ],
        ),
    )

    base_url = os.environ.get("EVALHUB_BASE_URL", "http://localhost:8080")
    insecure = os.environ.get("EVALHUB_INSECURE", "false").lower() == "true"
    wait_for_evalhub_ready(base_url, insecure)
    wait_for_mlflow_ready(insecure)

    with SyncEvalHubClient(
        base_url=base_url,
        auth_token=os.environ.get("EVALHUB_AUTH_TOKEN"),
        insecure=insecure,
        tenant=os.environ.get("EVALHUB_TENANT", "default"),
    ) as client:
        job = client.jobs.submit(request)

    print_json(
        {
            "status": "submitted",
            "job_id": job.id,
            "request_name": request.name,
            "benchmark_ids": benchmarks,
            "session_id": parameters["dataset"]["session_id"],
        }
    )


def wait_for_evalhub_ready(base_url: str, insecure: bool) -> None:
    timeout_seconds = int(os.environ.get("QUICKSTART_EVALHUB_READY_TIMEOUT_SECONDS", "600"))
    if timeout_seconds <= 0:
        return

    health_url = f"{base_url.rstrip('/')}/api/v1/health"
    deadline = time.monotonic() + timeout_seconds
    context = ssl._create_unverified_context() if insecure and health_url.startswith("https://") else None
    last_error = ""

    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=5, context=context) as response:
                if 200 <= response.status < 300:
                    print_json({"status": "evalhub_ready", "health_url": health_url})
                    return
                last_error = f"HTTP {response.status}"
        except (OSError, urllib.error.URLError) as exc:
            last_error = str(exc)
        print_json({"status": "waiting_for_evalhub", "health_url": health_url, "error": last_error})
        time.sleep(10)

    raise TimeoutError(f"EvalHub was not ready after {timeout_seconds} seconds: {last_error}")


def wait_for_mlflow_ready(insecure: bool) -> None:
    if os.environ.get("QUICKSTART_WAIT_FOR_MLFLOW", "false").lower() != "true":
        return
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI")
    if not tracking_uri:
        return

    timeout_seconds = int(os.environ.get("QUICKSTART_MLFLOW_READY_TIMEOUT_SECONDS", "600"))
    health_url = f"{tracking_uri.rstrip('/')}/health"
    deadline = time.monotonic() + timeout_seconds
    context = ssl._create_unverified_context() if insecure and health_url.startswith("https://") else None
    last_error = ""

    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=5, context=context) as response:
                if 200 <= response.status < 300:
                    print_json({"status": "mlflow_ready", "health_url": health_url})
                    return
                last_error = f"HTTP {response.status}"
        except (OSError, urllib.error.URLError) as exc:
            last_error = str(exc)
        print_json({"status": "waiting_for_mlflow", "health_url": health_url, "error": last_error})
        time.sleep(10)

    raise TimeoutError(f"MLflow was not ready after {timeout_seconds} seconds: {last_error}")


def load_fixture(path: str | Path) -> dict[str, Any]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("dataset"), dict):
        raise ValueError("Fixture must include a dataset JSON object")
    payload.setdefault("metadata", {})
    return payload


def select_benchmarks(raw: str, fixture: dict[str, Any]) -> list[str]:
    if raw == "auto":
        selected = list(ALWAYS_ENABLED_BENCHMARKS)
        if len(fixture["dataset"].get("conversation", [])) >= 5:
            selected.extend(LONG_SESSION_BENCHMARKS)
        return selected
    benchmarks = [item.strip() for item in raw.split(",") if item.strip()]
    unsupported = sorted(set(benchmarks) - set(SUPPORTED_BENCHMARKS))
    if unsupported:
        raise ValueError(f"Unsupported benchmark ids: {', '.join(unsupported)}")
    return benchmarks


def build_parameters(fixture: dict[str, Any], run_suffix: str | None = None) -> dict[str, Any]:
    dataset = copy.deepcopy(fixture["dataset"])
    metadata = copy.deepcopy(fixture.get("metadata", {}))
    metadata.setdefault("assistant_id", dataset.get("assistant_id", ""))
    metadata.setdefault("session_id", dataset.get("session_id", ""))
    metadata.setdefault("source", "gaussia.quickstart.agent-transcript.v1")
    if run_suffix:
        dataset["session_id"] = f"{dataset['session_id']}-{run_suffix}"
        metadata["session_id"] = dataset["session_id"]
        for key in ("stream_id", "control_id"):
            if metadata.get(key):
                metadata[key] = f"{metadata[key]}-{run_suffix}"
    return {"dataset": dataset, "metadata": metadata}


def model_name(fixture: dict[str, Any]) -> str:
    metadata = fixture.get("metadata", {})
    return (
        os.environ.get("GAUSSIA_EVALUATED_MODEL_NAME")
        or metadata.get("evaluated_model_name")
        or "support-agent-demo-v1"
    )


def model_url(fixture: dict[str, Any]) -> str:
    metadata = fixture.get("metadata", {})
    return (
        os.environ.get("GAUSSIA_EVALUATED_MODEL_URL")
        or metadata.get("evaluated_model_url")
        or "https://example.invalid/models/support-agent-demo-v1"
    )


def request_name(metadata: dict[str, Any]) -> str:
    return "-".join(
        value
        for value in (
            "gaussia-agent-eval",
            str(metadata.get("assistant_id", "")),
            str(metadata.get("session_id", "")),
            str(metadata.get("control_id", "")),
        )
        if value
    )[:120].rstrip("-")


def print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
