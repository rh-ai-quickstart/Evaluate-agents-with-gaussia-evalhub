"""Run evaluation page — submit fixtures to EvalHub via the SDK."""

from __future__ import annotations

import json

import streamlit as st

from config import BENCHMARKS_INFO
from services.evaluation_service import EvaluationService
from services.fixture_service import FixtureSummary


def render(
    *,
    evaluation_service: EvaluationService,
    fixtures: dict[str, FixtureSummary],
    selected_fixture: str,
) -> None:
    st.title("Run Evaluation")

    meta = fixtures[selected_fixture]
    st.markdown(
        f"Submit benchmarks for **{meta.title}** directly to the EvalHub API "
        "(no OpenShift submit Job)."
    )
    st.divider()

    _render_benchmarks()
    st.divider()

    humanity_only, unique_run = _render_run_config()
    st.divider()

    if st.button(
        f"Submit: {'Humanity only' if humanity_only else 'All benchmarks'}",
        type="primary",
        use_container_width=True,
    ):
        try:
            with st.spinner("Submitting to EvalHub…"):
                result = evaluation_service.submit_run(
                    humanity_only=humanity_only,
                    fixture=selected_fixture,
                    unique_run=unique_run,
                )
            st.success("Evaluation submitted.")
            st.json(result)
        except Exception as exc:  # noqa: BLE001 — surface API/config errors in UI
            st.error(f"Submission failed: {exc}")

    with st.expander("Dry run (preview request)"):
        st.caption("Build the JobSubmissionRequest without calling EvalHub.")
        if st.button("Preview request", use_container_width=True):
            try:
                result = evaluation_service.submit_run(
                    humanity_only=humanity_only,
                    fixture=selected_fixture,
                    unique_run=unique_run,
                    dry_run=True,
                )
                st.code(json.dumps(result, indent=2, sort_keys=True), language="json")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Dry run failed: {exc}")


def _render_benchmarks() -> None:
    st.subheader("Available Benchmarks")
    pills_html = ""
    for name, info in BENCHMARKS_INFO.items():
        pills_html += (
            f'<span class="benchmark-pill" '
            f'style="background:{info["color"]}22; color:{info["color"]}; '
            f'border:1px solid {info["color"]}44">'
            f"{name}</span>"
        )
    st.markdown(pills_html, unsafe_allow_html=True)
    st.markdown("")

    bench_cols = st.columns(3)
    for i, (name, info) in enumerate(BENCHMARKS_INFO.items()):
        with bench_cols[i % 3]:
            st.markdown(
                f"**{name}**  \n"
                f"{info['desc']}  \n"
                f"*{info['models']}*"
            )


def _render_run_config() -> tuple[bool, bool]:
    st.subheader("Run Configuration")
    run_type = st.radio(
        "Benchmark Scope",
        ["Humanity only", "All benchmarks"],
        horizontal=True,
        help=(
            "**Humanity only** requires no external models. "
            "**All benchmarks** requires judge and guardian models configured for the provider."
        ),
    )
    unique_run = st.checkbox(
        "Unique run suffix",
        value=True,
        help="Append a timestamp to session/stream/control ids so repeated submits stay distinct.",
    )
    return run_type == "Humanity only", unique_run
