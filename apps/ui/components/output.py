"""Helpers for displaying structured results in Streamlit widgets."""

from __future__ import annotations

import json
from typing import Any

import streamlit as st


def show_json(payload: Any, *, container=None) -> None:
    """Render a JSON-serializable payload in a Streamlit code block."""
    target = container if container is not None else st
    target.code(json.dumps(payload, indent=2, sort_keys=True, default=str), language="json")
