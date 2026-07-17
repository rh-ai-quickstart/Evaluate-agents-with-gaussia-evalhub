"""Sidebar navigation and shared controls."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import streamlit as st

from services.fixture_service import FixtureSummary


@dataclass(frozen=True)
class SidebarState:
    page: str
    selected_fixture: str


def render_sidebar(
    *,
    assets_dir: Path,
    fixtures: dict[str, FixtureSummary],
) -> SidebarState:
    fixture_names = list(fixtures.keys())

    with st.sidebar:
        st.image(str(assets_dir / "gaussia-evalhub-logo.png"))
        st.caption("Quickstart Dashboard")
        st.divider()

        page = st.radio(
            "Navigation",
            ["Fixtures", "Run Evaluation", "Jobs"],
            label_visibility="collapsed",
        )

        if page in ("Fixtures", "Run Evaluation"):
            st.divider()
            st.markdown("**Selected Fixture**")
            if not fixture_names:
                st.error("No fixtures found in apps/evalhub_job_submission/fixtures.")
                st.stop()
            selected_fixture = st.selectbox(
                "Fixture",
                fixture_names,
                format_func=lambda name: fixtures[name].title,
                label_visibility="collapsed",
            )
        else:
            selected_fixture = fixture_names[0] if fixture_names else ""

    return SidebarState(
        page=page,
        selected_fixture=selected_fixture,
    )
