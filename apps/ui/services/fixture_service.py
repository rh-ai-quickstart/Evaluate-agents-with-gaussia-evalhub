"""Discover and load EvalHub scenario fixtures from disk."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FixtureSummary:
    """Display-oriented view of a fixture discovered on disk."""

    name: str
    title: str
    summary: str
    path: Path


class FixtureService:
    """Load scenario fixtures from ``apps/evalhub_job_submission/fixtures``."""

    def __init__(self, fixtures_dir: Path) -> None:
        self._fixtures_dir = fixtures_dir

    @property
    def fixtures_dir(self) -> Path:
        return self._fixtures_dir

    def list_names(self) -> list[str]:
        return [fixture.name for fixture in self.list_fixtures()]

    def list_fixtures(self) -> list[FixtureSummary]:
        if not self._fixtures_dir.is_dir():
            return []

        fixtures: list[FixtureSummary] = []
        for path in sorted(self._fixtures_dir.glob("*.json")):
            payload = self._read_json(path)
            fixtures.append(self._to_summary(path, payload))
        return fixtures

    def get_summary(self, name: str) -> FixtureSummary:
        path = self._path_for(name)
        return self._to_summary(path, self._read_json(path))

    def load(self, name: str) -> dict[str, Any]:
        return self._read_json(self._path_for(name))

    def _path_for(self, name: str) -> Path:
        path = self._fixtures_dir / f"{name}.json"
        if not path.is_file():
            raise FileNotFoundError(f"Fixture not found: {path}")
        return path

    @staticmethod
    def _read_json(path: Path) -> dict[str, Any]:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"Fixture must be a JSON object: {path}")
        return payload

    @staticmethod
    def _to_summary(path: Path, payload: dict[str, Any]) -> FixtureSummary:
        name = path.stem
        metadata = payload.get("metadata") or {}
        dataset = payload.get("dataset") or {}
        scenario = str(metadata.get("scenario") or name)
        context = str(dataset.get("context") or "").strip()

        return FixtureSummary(
            name=name,
            title=FixtureService._humanize(scenario),
            summary=FixtureService._summarize(context),
            path=path,
        )

    @staticmethod
    def _humanize(slug: str) -> str:
        return slug.replace("-", " ").replace("_", " ").strip().title()

    @staticmethod
    def _summarize(context: str, max_chars: int = 180) -> str:
        if not context:
            return "No scenario context provided."

        first_sentence = context.split(". ", 1)[0].strip()
        if first_sentence and not first_sentence.endswith("."):
            first_sentence = f"{first_sentence}."

        if len(first_sentence) <= max_chars:
            return first_sentence
        return f"{first_sentence[: max_chars - 1].rstrip()}…"
