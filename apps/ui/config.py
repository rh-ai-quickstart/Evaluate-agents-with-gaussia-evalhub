"""UI paths and static configuration."""

from __future__ import annotations

from pathlib import Path

from services.fixture_service import FixtureService

UI_DIR = Path(__file__).resolve().parent
REPO_ROOT = UI_DIR.parents[1]
ASSETS_DIR = UI_DIR / "assets"
JOB_SUBMISSION_DIR = REPO_ROOT / "apps" / "evalhub_job_submission"
FIXTURES_DIR = JOB_SUBMISSION_DIR / "fixtures"

BENCHMARKS_INFO: dict[str, dict[str, str]] = {
    "humanity": {
        "desc": "Emotional tone and entropy across assistant replies",
        "models": "None required",
        "color": "#27ae60",
    },
    "context": {
        "desc": "Answer alignment with conversation context",
        "models": "Judge model",
        "color": "#2980b9",
    },
    "conversational": {
        "desc": "Dialogue quality — memory, Grice maxims, sensibleness",
        "models": "Judge model",
        "color": "#8e44ad",
    },
    "agentic": {
        "desc": "Match to ground-truth expected answers",
        "models": "Judge model",
        "color": "#d35400",
    },
    "bias": {
        "desc": "Bias across protected attributes (gender, race, …)",
        "models": "Guardian model",
        "color": "#c0392b",
    },
    "toxicity": {
        "desc": "Toxic language and harmful associations",
        "models": "Embeddings / lexicon",
        "color": "#7f8c8d",
    },
}


def build_fixture_service() -> FixtureService:
    return FixtureService(FIXTURES_DIR)
