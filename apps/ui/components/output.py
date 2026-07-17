"""Helpers for streaming make output into Streamlit widgets."""

from __future__ import annotations

from collections.abc import Callable

import streamlit as st


def streamlit_code_sink(container=None) -> Callable[[str], None]:
    """Return an ``on_output`` callback that writes into a Streamlit code block."""
    if container is None:
        container = st.empty()

    def on_output(text: str) -> None:
        container.code(text, language="bash")

    return on_output
