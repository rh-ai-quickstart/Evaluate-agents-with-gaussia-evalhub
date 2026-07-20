"""Jobs page — list and inspect EvalHub evaluation jobs via the API."""

from __future__ import annotations

import os

import streamlit as st

from services.evaluation_service import EvaluationService


def render(*, evaluation_service: EvaluationService) -> None:
    st.title("Jobs")
    st.markdown(
        "Inspect evaluations already submitted to EvalHub. "
        "Cluster submit Jobs are only created by Make targets such as "
        "`make run-humanity` / `make run-all`."
    )

    _render_connection()
    st.divider()

    st.subheader("Recent jobs")
    limit = st.slider("Limit", min_value=5, max_value=50, value=20, step=5)
    if st.button("Refresh job list", type="primary", use_container_width=True):
        try:
            with st.spinner("Fetching jobs…"):
                jobs = evaluation_service.list_jobs(limit=limit)
            if not jobs:
                st.info("No jobs returned.")
            else:
                st.dataframe(jobs, use_container_width=True)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Failed to list jobs: {exc}")

    st.divider()
    st.subheader("Job detail")
    job_id = st.text_input("Job ID", placeholder="Paste an EvalHub job id")
    if st.button("Get job", use_container_width=True, disabled=not job_id.strip()):
        try:
            with st.spinner("Fetching job…"):
                job = evaluation_service.get_job(job_id.strip())
            st.json(job)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Failed to get job: {exc}")


def _render_connection() -> None:
    base_url = os.environ.get("EVALHUB_BASE_URL", "(unset — load .env or UI ConfigMap)")
    tenant = os.environ.get("EVALHUB_TENANT", "default")
    insecure = os.environ.get("EVALHUB_INSECURE", "false")
    token_set = bool(
        os.environ.get("EVALHUB_AUTH_TOKEN") or os.environ.get("EVALHUB_AUTH_TOKEN_PATH")
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("EvalHub URL", _short(base_url, 28))
    c2.metric("Tenant", tenant)
    c3.metric("Insecure TLS", insecure)
    c4.metric("Auth token", "set" if token_set else "unset")


def _short(value: str, max_len: int) -> str:
    if len(value) <= max_len:
        return value
    return f"{value[: max_len - 1]}…"
