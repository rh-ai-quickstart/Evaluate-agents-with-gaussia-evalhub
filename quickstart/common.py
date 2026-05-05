from __future__ import annotations

import copy
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ALWAYS_ENABLED_BENCHMARKS = ("humanity", "context", "conversational")
LONG_SESSION_BENCHMARKS = ("bias", "toxicity")
SUPPORTED_BENCHMARKS = (*ALWAYS_ENABLED_BENCHMARKS, *LONG_SESSION_BENCHMARKS)
DEFAULT_MODEL_NAME = "support-agent-demo-v1"
DEFAULT_MODEL_URL = "https://example.invalid/models/support-agent-demo-v1"


def load_quickstart_fixture(path: str | Path) -> dict[str, Any]:
    fixture_path = Path(path)
    try:
        payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Fixture not found: {fixture_path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Fixture is not valid JSON: {fixture_path}") from exc

    if not isinstance(payload, dict):
        raise ValueError("Fixture must be a JSON object")
    if not isinstance(payload.get("dataset"), dict):
        raise ValueError("Fixture must include a dataset JSON object")

    metadata = payload.setdefault("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("Fixture metadata must be a JSON object")
    return payload


def selected_benchmarks(raw_benchmarks: str, fixture: dict[str, Any]) -> list[str]:
    if raw_benchmarks == "auto":
        count = len(fixture["dataset"].get("conversation", []))
        selected = list(ALWAYS_ENABLED_BENCHMARKS)
        if count >= 5:
            selected.extend(LONG_SESSION_BENCHMARKS)
        return selected

    benchmarks = [item.strip() for item in raw_benchmarks.split(",") if item.strip()]
    unsupported = sorted(set(benchmarks) - set(SUPPORTED_BENCHMARKS))
    if unsupported:
        raise ValueError(f"Unsupported benchmark ids: {', '.join(unsupported)}")
    if not benchmarks:
        raise ValueError("--benchmarks must include at least one benchmark id")
    return benchmarks


def build_evalhub_parameters(
    fixture: dict[str, Any],
    *,
    run_suffix: str | None = None,
) -> dict[str, Any]:
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

    return {
        "dataset": dataset,
        "metadata": metadata,
    }


def evaluated_model_name(fixture: dict[str, Any]) -> str:
    metadata = fixture.get("metadata", {})
    return (
        os.environ.get("GAUSSIA_EVALUATED_MODEL_NAME")
        or metadata.get("evaluated_model_name")
        or DEFAULT_MODEL_NAME
    )


def evaluated_model_url(fixture: dict[str, Any]) -> str:
    metadata = fixture.get("metadata", {})
    return (
        os.environ.get("GAUSSIA_EVALUATED_MODEL_URL")
        or metadata.get("evaluated_model_url")
        or DEFAULT_MODEL_URL
    )


def generated_run_suffix() -> str:
    return datetime.now(tz=UTC).strftime("%Y%m%d%H%M%S")


def print_json(payload: Any) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))
