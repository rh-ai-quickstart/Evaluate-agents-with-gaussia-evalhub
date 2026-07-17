"""Global Streamlit CSS for the dashboard."""

from __future__ import annotations

import streamlit as st

GLOBAL_CSS = """
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
"""


def apply_global_styles() -> None:
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)
