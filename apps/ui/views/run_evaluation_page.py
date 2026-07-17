"""Run evaluation page."""

from __future__ import annotations

import streamlit as st

from components.output import streamlit_code_sink
from config import BENCHMARKS_INFO
from services.evaluation_service import EvaluationService
from services.fixture_service import FixtureSummary


def render(
    *,
    evaluation_service: EvaluationService,
    fixtures: dict[str, FixtureSummary],
    selected_fixture: str,
    namespace: str,
    release: str,
) -> None:
    st.title("Run Evaluation")

    meta = fixtures[selected_fixture]
    st.markdown(f"Submit benchmarks against the **{meta.title}** fixture.")
    st.divider()

    _render_benchmarks()
    st.divider()

    run_name, humanity_only, resources = _render_run_config(evaluation_service)
    st.divider()

    if st.button(
        f"Submit: {'Humanity only' if humanity_only else 'All benchmarks'}",
        type="primary",
        use_container_width=True,
    ):
        evaluation_service.submit_run(
            humanity_only=humanity_only,
            namespace=namespace,
            release=release,
            fixture=selected_fixture,
            run_name=run_name,
            on_output=streamlit_code_sink(),
            **resources,
        )

    st.divider()
    _render_advanced(
        evaluation_service=evaluation_service,
        selected_fixture=selected_fixture,
        namespace=namespace,
        release=release,
        run_name=run_name,
        resources=resources,
    )


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


def _render_run_config(
    evaluation_service: EvaluationService,
) -> tuple[str, bool, dict[str, str]]:
    st.subheader("Run Configuration")
    cfg_left, cfg_right = st.columns(2)

    with cfg_left:
        run_name = st.text_input(
            "Run Name",
            value=evaluation_service.generate_run_name(),
            help="Unique identifier for this run. Auto-generated with a UTC timestamp.",
        )

    with cfg_right:
        run_type = st.radio(
            "Benchmark Scope",
            ["Humanity only", "All benchmarks"],
            horizontal=True,
            help=(
                "**Humanity only** requires no external models. "
                "**All benchmarks** requires judge and guardian models configured in `.env`."
            ),
        )

    with st.expander("Resource Limits"):
        r1, r2, r3, r4 = st.columns(4)
        cpu_request = r1.text_input("CPU Request", value="250m", key="cpu_req")
        memory_request = r2.text_input("Memory Request", value="512Mi", key="mem_req")
        cpu_limit = r3.text_input("CPU Limit", value="1", key="cpu_lim")
        memory_limit = r4.text_input("Memory Limit", value="1Gi", key="mem_lim")

    return (
        run_name,
        run_type == "Humanity only",
        {
            "cpu_request": cpu_request,
            "memory_request": memory_request,
            "cpu_limit": cpu_limit,
            "memory_limit": memory_limit,
        },
    )


def _render_advanced(
    *,
    evaluation_service: EvaluationService,
    selected_fixture: str,
    namespace: str,
    release: str,
    run_name: str,
    resources: dict[str, str],
) -> None:
    with st.expander("Advanced"):
        st.markdown(
            "**External EvalHub** — submit against an existing EvalHub "
            "(uses `EVALHUB_*` from `.env`)."
        )
        if st.button("Run against external EvalHub", use_container_width=True):
            evaluation_service.run_external(
                namespace=namespace,
                release=release,
                fixture=selected_fixture,
                run_name=run_name,
                on_output=streamlit_code_sink(),
                **resources,
            )

        st.markdown("")
        st.markdown(
            "**Local run (uv)** — submit from your workstation. "
            "Requires `EVALHUB_*` in `.env`."
        )
        if st.button("Run locally with uv", use_container_width=True):
            evaluation_service.run_local(
                fixture=selected_fixture,
                on_output=streamlit_code_sink(),
            )
