"""Shared HTML helpers for Streamlit markdown rendering."""

from __future__ import annotations

import html


def escape(text: str) -> str:
    return html.escape(str(text))
