"""Sidebar navigation and shared controls."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import streamlit as st

from config import DEFAULT_NAMESPACE, DEFAULT_RELEASE
from services.fixture_service import FixtureSummary


@dataclass(frozen=True)
class SidebarState:
    page: str
    selected_fixture: str
    namespace: str
    release: str


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
            ["Fixtures", "Run Evaluation", "Run History & Logs"],
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

        st.divider()
        st.caption("Cluster Settings")
        namespace = st.text_input("Namespace", value=DEFAULT_NAMESPACE, key="ns")
        release = st.text_input("Release", value=DEFAULT_RELEASE, key="rel")

    return SidebarState(
        page=page,
        selected_fixture=selected_fixture,
        namespace=namespace,
        release=release,
    )
