"""Gaussia EvalHub Quickstart — Streamlit dashboard.

Browse agent conversation fixtures and submit evaluation runs.
Environment setup and platform installation are handled via the CLI
(see README.md); this UI focuses on inspecting fixtures and running
benchmarks.
"""

from __future__ import annotations

import streamlit as st

from clients.make_client import MakeClient
from components.sidebar import render_sidebar
from components.styles import apply_global_styles
from config import ASSETS_DIR, REPO_ROOT, build_fixture_service
from views import fixtures_page, run_evaluation_page, run_history_page
from services.evaluation_service import EvaluationService

st.set_page_config(
    page_title="Gaussia EvalHub",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_global_styles()

fixture_service = build_fixture_service()
fixtures = {fixture.name: fixture for fixture in fixture_service.list_fixtures()}
evaluation_service = EvaluationService(MakeClient(REPO_ROOT))

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
        namespace=sidebar.namespace,
        release=sidebar.release,
    )
elif sidebar.page == "Run History & Logs":
    run_history_page.render(
        evaluation_service=evaluation_service,
        namespace=sidebar.namespace,
        release=sidebar.release,
    )
