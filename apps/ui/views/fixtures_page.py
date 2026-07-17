"""Fixtures browser page."""

from __future__ import annotations

from typing import Any

import streamlit as st

from components.html import escape
from services.fixture_service import FixtureService, FixtureSummary


def render(
    *,
    fixture_service: FixtureService,
    fixtures: dict[str, FixtureSummary],
    selected_fixture: str,
) -> None:
    st.title("Agent Conversation Fixtures")
    st.markdown(
        "Each fixture is a recorded agent conversation used as input for "
        "Gaussia benchmarks. Select a fixture from the sidebar to inspect it."
    )
    st.divider()

    _render_cards(fixtures, selected_fixture)
    st.divider()

    data = fixture_service.load(selected_fixture)
    dataset = data["dataset"]
    metadata = data["metadata"]
    meta = fixtures[selected_fixture]
    conversation = dataset["conversation"]

    st.header(meta.title)

    info_cols = st.columns(4)
    info_cols[0].metric("Interactions", len(conversation))
    info_cols[1].metric("Language", dataset["language"].title())
    info_cols[2].metric("Scenario", metadata["scenario"])
    info_cols[3].metric("Model", metadata["evaluated_model_name"])

    st.divider()
    _render_context(dataset["context"])
    _render_metadata_table(dataset, metadata)

    st.divider()
    _render_conversation(conversation)

    st.divider()
    with st.expander("Raw JSON"):
        st.json(data)


def _render_cards(
    fixtures: dict[str, FixtureSummary],
    selected_fixture: str,
) -> None:
    cols = st.columns(min(3, len(fixtures)) or 1)
    for i, fixture in enumerate(fixtures.values()):
        with cols[i % len(cols)]:
            active = " border-color: #e74c3c;" if fixture.name == selected_fixture else ""
            st.markdown(
                f"""<div class="fixture-card" style="{active}">
                <h4>{escape(fixture.title)}</h4>
                <p>{escape(fixture.summary)}</p>
                </div>""",
                unsafe_allow_html=True,
            )


def _render_context(context: str) -> None:
    st.subheader("Scenario Context")
    st.markdown(
        f'<div class="context-box"><strong>Context —</strong> {escape(context)}</div>',
        unsafe_allow_html=True,
    )


def _render_metadata_table(
    dataset: dict[str, Any],
    metadata: dict[str, Any],
) -> None:
    with st.expander("Fixture Metadata"):
        rows = "".join(
            f"<tr><td>{escape(key)}</td><td><code>{escape(value)}</code></td></tr>"
            for key, value in {
                "Session ID": dataset["session_id"],
                "Assistant ID": dataset["assistant_id"],
                "Source": metadata["source"],
                "Stream ID": metadata["stream_id"],
                "Control ID": metadata["control_id"],
                "Agentspace": metadata["agentspace_id"],
                "Model URL": metadata["evaluated_model_url"],
            }.items()
        )
        st.markdown(
            f'<table class="meta-table">{rows}</table>',
            unsafe_allow_html=True,
        )


def _render_conversation(conversation: list[dict[str, Any]]) -> None:
    st.subheader("Conversation")
    show_ground_truth = st.toggle("Show ground-truth responses", value=False)

    for turn in conversation:
        qa_id = turn["qa_id"]
        st.markdown(
            f"""<div class="chat-bubble chat-user">
            <span class="chat-id">{escape(qa_id)}</span>
            <div class="chat-role chat-role-user">User</div>
            {escape(turn["query"])}
            </div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""<div class="chat-bubble chat-assistant">
            <div class="chat-role chat-role-asst">Assistant</div>
            {escape(turn["assistant"])}
            </div>""",
            unsafe_allow_html=True,
        )
        if show_ground_truth:
            st.markdown(
                f"""<div class="chat-bubble chat-ground-truth">
                <div class="chat-role chat-role-gt">Ground Truth</div>
                {escape(turn["ground_truth_assistant"])}
                </div>""",
                unsafe_allow_html=True,
            )
