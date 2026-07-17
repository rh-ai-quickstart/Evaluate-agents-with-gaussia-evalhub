"""Gaussia EvalHub Quickstart — Streamlit dashboard.

Browse agent conversation fixtures and submit evaluation runs via the
EvalHub API. Cluster submit Jobs remain a Make-only workflow
(``make run-humanity`` / ``make run-all``).
"""

from __future__ import annotations

import sys

import streamlit as st

from clients.evalhub_job_client import EvalHubJobClient
from components.sidebar import render_sidebar
from components.styles import apply_global_styles
from config import (
    ASSETS_DIR,
    FIXTURES_DIR,
    JOB_SUBMISSION_DIR,
    REPO_ROOT,
    build_fixture_service,
)
from services.evaluation_service import EvaluationService
from views import fixtures_page, jobs_page, run_evaluation_page

st.set_page_config(
    page_title="Gaussia EvalHub",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_global_styles()

# Shared submit helpers live as scripts under apps/evalhub_job_submission.
if str(JOB_SUBMISSION_DIR) not in sys.path:
    sys.path.insert(0, str(JOB_SUBMISSION_DIR))
from common import load_env_files  # noqa: E402

load_env_files(REPO_ROOT / ".env", JOB_SUBMISSION_DIR / ".env")

fixture_service = build_fixture_service()
fixtures = {fixture.name: fixture for fixture in fixture_service.list_fixtures()}
evaluation_service = EvaluationService(EvalHubJobClient(FIXTURES_DIR))

sidebar = render_sidebar(assets_dir=ASSETS_DIR, fixtures=fixtures)

if sidebar.page == "Fixtures":
    fixtures_page.render(
        fixture_service=fixture_service,
        fixtures=fixtures,
        selected_fixture=sidebar.selected_fixture,
    )
elif sidebar.page == "Run Evaluation":
    run_evaluation_page.render(
        evaluation_service=evaluation_service,
        fixtures=fixtures,
        selected_fixture=sidebar.selected_fixture,
    )
elif sidebar.page == "Jobs":
    jobs_page.render(evaluation_service=evaluation_service)
