"""Run history and logs page."""

from __future__ import annotations

import streamlit as st

from components.output import streamlit_code_sink
from services.evaluation_service import EvaluationService


def render(
    *,
    evaluation_service: EvaluationService,
    namespace: str,
    release: str,
) -> None:
    st.title("Run History & Logs")

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Platform Resources")
        if st.button("Validate resources", use_container_width=True):
            evaluation_service.validate(
                namespace=namespace,
                release=release,
                on_output=streamlit_code_sink(),
            )

    with col_b:
        st.subheader("Helm Releases")
        if st.button("List Helm releases", use_container_width=True):
            evaluation_service.list_releases(
                namespace=namespace,
                release=release,
                on_output=streamlit_code_sink(),
            )

    st.divider()

    st.subheader("Job Logs")
    log_run = st.text_input(
        "Run Name",
        placeholder="e.g. gaussia-evalhub-run-20260714120000",
        key="log_run",
    )

    l1, l2 = st.columns(2)
    with l1:
        if st.button("Follow logs", use_container_width=True, disabled=not log_run):
            evaluation_service.follow_logs(
                namespace=namespace,
                run_name=log_run,
                on_output=streamlit_code_sink(),
            )
    with l2:
        if st.button("Wait for run", use_container_width=True, disabled=not log_run):
            evaluation_service.wait_for_run(
                namespace=namespace,
                run_name=log_run,
                on_output=streamlit_code_sink(),
            )

    st.divider()

    st.subheader("Remove a Run")
    del_run = st.text_input(
        "Run Name to remove",
        placeholder="e.g. gaussia-evalhub-run-20260714120000",
        key="del_run",
    )
    if st.button("Uninstall run", use_container_width=True, disabled=not del_run):
        evaluation_service.uninstall_run(
            namespace=namespace,
            run_name=del_run,
            on_output=streamlit_code_sink(),
        )
