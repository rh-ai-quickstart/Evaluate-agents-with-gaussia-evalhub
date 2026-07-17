"""Gaussia EvalHub Quickstart — Streamlit dashboard.

Browse agent conversation fixtures and submit evaluation runs.
Environment setup and platform installation are handled via the CLI
(see README.md); this UI focuses on inspecting fixtures and running
benchmarks.
"""

from __future__ import annotations

import html
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import streamlit as st

UI_DIR = Path(__file__).resolve().parent
REPO_ROOT = UI_DIR.parents[1]
FIXTURES_DIR = REPO_ROOT / "apps" / "evalhub_job_submission" / "fixtures"

FIXTURE_META = {
    "first-line-support": {
        "title": "First-Line IT Support",
        "icon": "🖥️",
        "summary": (
            "A marketing manager contacts IT support about a VPN connection "
            "failure before an urgent customer presentation."
        ),
    },
    "retail": {
        "title": "Retail Customer Service",
        "icon": "🛒",
        "summary": (
            "A returning customer shops for a birthday gift while also "
            "escalating an unresolved missing-package issue."
        ),
    },
    "root-cause-analysis": {
        "title": "SRE Root-Cause Analysis",
        "icon": "🔍",
        "summary": (
            "An SRE investigates a 47-minute payment-processing outage, "
            "tracing it from deploy history through mesh logs to a stale "
            "sidecar version."
        ),
    },
}

BENCHMARKS_INFO = {
    "humanity": {
        "desc": "Emotional tone and entropy across assistant replies",
        "models": "None required",
        "color": "#27ae60",
    },
    "context": {
        "desc": "Answer alignment with conversation context",
        "models": "Judge model",
        "color": "#2980b9",
    },
    "conversational": {
        "desc": "Dialogue quality — memory, Grice maxims, sensibleness",
        "models": "Judge model",
        "color": "#8e44ad",
    },
    "agentic": {
        "desc": "Match to ground-truth expected answers",
        "models": "Judge model",
        "color": "#d35400",
    },
    "bias": {
        "desc": "Bias across protected attributes (gender, race, …)",
        "models": "Guardian model",
        "color": "#c0392b",
    },
    "toxicity": {
        "desc": "Toxic language and harmful associations",
        "models": "Embeddings / lexicon",
        "color": "#7f8c8d",
    },
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_fixture(name: str) -> dict:
    path = FIXTURES_DIR / f"{name}.json"
    return json.loads(path.read_text())


def _generate_run_name() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"gaussia-evalhub-run-{ts}"


def _run_make(
    target: str,
    extra_vars: dict[str, str] | None = None,
    output_container=None,
) -> tuple[int, str]:
    cmd = ["make", "-C", str(REPO_ROOT), target]
    if extra_vars:
        for k, v in extra_vars.items():
            cmd.append(f"{k}={v}")

    if output_container is None:
        output_container = st.empty()

    collected: list[str] = []
    cmd_str = " ".join(cmd)
    output_container.code(f"$ {cmd_str}\n\nRunning…", language="bash")

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=str(REPO_ROOT),
        )
        for line in iter(proc.stdout.readline, ""):
            collected.append(line)
            output_container.code(
                f"$ {cmd_str}\n\n{''.join(collected)}", language="bash"
            )
        proc.wait()
        if not collected:
            collected.append("(no output)\n")
    except FileNotFoundError:
        collected.append("ERROR: 'make' not found. Ensure GNU Make is installed.\n")
        proc = None

    full = "".join(collected)
    rc = proc.returncode if proc else 1
    status = "Done" if rc == 0 else f"Exit code {rc}"
    output_container.code(f"$ {cmd_str}\n\n{full}\n\n{status}", language="bash")
    return rc, full


def _esc(text: str) -> str:
    return html.escape(text)


# ---------------------------------------------------------------------------
# Page config & global styles
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Gaussia EvalHub",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; }
    div[data-testid="stSidebar"] { background-color: #131720; }

    .fixture-card {
        background: #1a1f2e;
        border-radius: 10px;
        padding: 1.3rem 1.5rem;
        margin-bottom: 1rem;
        border-left: 4px solid #e74c3c;
    }
    .fixture-card h4 { margin: 0 0 0.3rem 0; }
    .fixture-card p  { margin: 0; color: #aaa; font-size: 0.92em; }

    .benchmark-pill {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.82em;
        font-weight: 600;
        margin: 0.2rem 0.3rem 0.2rem 0;
    }

    .chat-bubble {
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.6rem;
        line-height: 1.55;
        font-size: 0.93em;
    }
    .chat-user {
        background: #1e2738;
        border-left: 3px solid #3498db;
        margin-right: 3rem;
    }
    .chat-assistant {
        background: #1a2a1a;
        border-left: 3px solid #27ae60;
        margin-left: 3rem;
    }
    .chat-ground-truth {
        background: #2a1a2a;
        border-left: 3px solid #8e44ad;
        margin-left: 3rem;
    }
    .chat-role {
        font-size: 0.78em;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 0.35rem;
    }
    .chat-role-user     { color: #3498db; }
    .chat-role-asst     { color: #27ae60; }
    .chat-role-gt       { color: #8e44ad; }
    .chat-id {
        font-size: 0.72em;
        color: #555;
        float: right;
        margin-top: 2px;
    }

    .context-box {
        background: #1a1f2e;
        border: 1px solid #2c3345;
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        margin-bottom: 1.5rem;
        line-height: 1.6;
        font-size: 0.93em;
        color: #ccc;
    }
    .context-box strong { color: #e74c3c; }

    .meta-table {
        width: 100%;
        font-size: 0.88em;
    }
    .meta-table td {
        padding: 0.35rem 0.6rem;
        border-bottom: 1px solid #222;
    }
    .meta-table td:first-child {
        color: #888;
        white-space: nowrap;
        width: 180px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

ASSETS_DIR = UI_DIR / "assets"

with st.sidebar:
    st.image(str(ASSETS_DIR / "gaussia-evalhub-logo.png"))
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
        selected_fixture = st.selectbox(
            "Fixture",
            list(FIXTURE_META.keys()),
            format_func=lambda k: f"{FIXTURE_META[k]['icon']}  {FIXTURE_META[k]['title']}",
            label_visibility="collapsed",
        )
    else:
        selected_fixture = list(FIXTURE_META.keys())[0]

    st.divider()
    st.caption("Cluster Settings")
    namespace = st.text_input("Namespace", value="gaussia-evalhub-quickstart", key="ns")
    release = st.text_input("Release", value="gaussia-evalhub", key="rel")


# ---------------------------------------------------------------------------
# Fixtures page
# ---------------------------------------------------------------------------

if page == "Fixtures":
    st.title("Agent Conversation Fixtures")
    st.markdown(
        "Each fixture is a recorded agent conversation used as input for "
        "Gaussia benchmarks. Select a fixture from the sidebar to inspect it."
    )
    st.divider()

    # --- Fixture cards overview ---
    cols = st.columns(3)
    for i, (key, meta) in enumerate(FIXTURE_META.items()):
        with cols[i]:
            active = " border-color: #e74c3c;" if key == selected_fixture else ""
            st.markdown(
                f"""<div class="fixture-card" style="{active}">
                <h4>{meta['icon']}  {meta['title']}</h4>
                <p>{meta['summary']}</p>
                </div>""",
                unsafe_allow_html=True,
            )

    st.divider()

    # --- Selected fixture detail ---
    data = _load_fixture(selected_fixture)
    dataset = data["dataset"]
    metadata = data["metadata"]
    meta = FIXTURE_META[selected_fixture]
    conversation = dataset["conversation"]

    st.header(f"{meta['icon']}  {meta['title']}")

    # Metadata
    info_cols = st.columns(4)
    info_cols[0].metric("Interactions", len(conversation))
    info_cols[1].metric("Language", dataset["language"].title())
    info_cols[2].metric("Scenario", metadata["scenario"])
    info_cols[3].metric("Model", metadata["evaluated_model_name"])

    st.divider()

    # Context
    st.subheader("Scenario Context")
    st.markdown(
        f'<div class="context-box"><strong>Context —</strong> {_esc(dataset["context"])}</div>',
        unsafe_allow_html=True,
    )

    # Metadata table
    with st.expander("Fixture Metadata"):
        rows = "".join(
            f"<tr><td>{_esc(k)}</td><td><code>{_esc(v)}</code></td></tr>"
            for k, v in {
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

    st.divider()

    # Conversation
    st.subheader("Conversation")

    show_ground_truth = st.toggle("Show ground-truth responses", value=False)

    for turn in conversation:
        qa_id = turn["qa_id"]

        # User message
        st.markdown(
            f"""<div class="chat-bubble chat-user">
            <span class="chat-id">{_esc(qa_id)}</span>
            <div class="chat-role chat-role-user">User</div>
            {_esc(turn['query'])}
            </div>""",
            unsafe_allow_html=True,
        )

        # Assistant response
        st.markdown(
            f"""<div class="chat-bubble chat-assistant">
            <div class="chat-role chat-role-asst">Assistant</div>
            {_esc(turn['assistant'])}
            </div>""",
            unsafe_allow_html=True,
        )

        # Ground truth (optional)
        if show_ground_truth:
            st.markdown(
                f"""<div class="chat-bubble chat-ground-truth">
                <div class="chat-role chat-role-gt">Ground Truth</div>
                {_esc(turn['ground_truth_assistant'])}
                </div>""",
                unsafe_allow_html=True,
            )

    st.divider()

    # Raw JSON
    with st.expander("Raw JSON"):
        st.json(data)


# ---------------------------------------------------------------------------
# Run Evaluation page
# ---------------------------------------------------------------------------

elif page == "Run Evaluation":
    st.title("Run Evaluation")

    meta = FIXTURE_META[selected_fixture]
    st.markdown(
        f"Submit benchmarks against the **{meta['icon']} {meta['title']}** fixture."
    )

    st.divider()

    # --- Benchmark info ---
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

    st.divider()

    # --- Run config ---
    st.subheader("Run Configuration")
    cfg_left, cfg_right = st.columns(2)

    with cfg_left:
        run_name = st.text_input(
            "Run Name",
            value=_generate_run_name(),
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
        cpu_req = r1.text_input("CPU Request", value="250m", key="cpu_req")
        mem_req = r2.text_input("Memory Request", value="512Mi", key="mem_req")
        cpu_lim = r3.text_input("CPU Limit", value="1", key="cpu_lim")
        mem_lim = r4.text_input("Memory Limit", value="1Gi", key="mem_lim")

    st.divider()

    # --- Run buttons ---
    extra_vars = {
        "NAMESPACE": namespace,
        "RELEASE": release,
        "FIXTURE": selected_fixture,
        "RUN_NAME": run_name,
        "JOB_CPU_REQUEST": cpu_req,
        "JOB_MEMORY_REQUEST": mem_req,
        "JOB_CPU_LIMIT": cpu_lim,
        "JOB_MEMORY_LIMIT": mem_lim,
    }

    target = "run-humanity" if run_type == "Humanity only" else "run-all"

    if st.button(
        f"Submit: {run_type}",
        type="primary",
        use_container_width=True,
    ):
        out = st.empty()
        _run_make(target, extra_vars, out)

    st.divider()

    # --- Advanced ---
    with st.expander("Advanced"):
        st.markdown("**External EvalHub** — submit against an existing EvalHub (uses `EVALHUB_*` from `.env`).")
        if st.button("Run against external EvalHub", use_container_width=True):
            out = st.empty()
            _run_make("install-external", extra_vars, out)

        st.markdown("")
        st.markdown("**Local run (uv)** — submit from your workstation. Requires `EVALHUB_*` in `.env`.")
        if st.button("Run locally with uv", use_container_width=True):
            out = st.empty()
            _run_make("run-local", {"FIXTURE": selected_fixture}, out)


# ---------------------------------------------------------------------------
# Run History & Logs page
# ---------------------------------------------------------------------------

elif page == "Run History & Logs":
    st.title("Run History & Logs")

    extra = {"NAMESPACE": namespace, "RELEASE": release}

    col_a, col_b = st.columns(2)
    with col_a:
        st.subheader("Platform Resources")
        if st.button("Validate resources", use_container_width=True):
            out = st.empty()
            _run_make("validate", extra, out)

    with col_b:
        st.subheader("Helm Releases")
        if st.button("List Helm releases", use_container_width=True):
            out = st.empty()
            _run_make("list-releases", extra, out)

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
            out = st.empty()
            _run_make("logs", {"NAMESPACE": namespace, "RUN_NAME": log_run}, out)
    with l2:
        if st.button("Wait for run", use_container_width=True, disabled=not log_run):
            out = st.empty()
            _run_make("wait-run", {"NAMESPACE": namespace, "RUN_NAME": log_run}, out)

    st.divider()

    st.subheader("Remove a Run")
    del_run = st.text_input(
        "Run Name to remove",
        placeholder="e.g. gaussia-evalhub-run-20260714120000",
        key="del_run",
    )
    if st.button("Uninstall run", use_container_width=True, disabled=not del_run):
        out = st.empty()
        _run_make("uninstall-run", {"NAMESPACE": namespace, "RUN_NAME": del_run}, out)
