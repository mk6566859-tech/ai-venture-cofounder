"""Human-readable rendering helpers for structured agent and application data."""
import html
import json
import re
from typing import Any

import streamlit as st

from utils.formatters import clean_markdown_json


_LABEL_OVERRIDES = {
    "cac": "Customer Acquisition Cost (CAC)",
    "tam": "Total Addressable Market (TAM)",
    "usp": "Unique Selling Proposition (USP)",
    "ai": "AI",
    "api": "API",
    "m6": "Month 6",
    "y1": "Year 1",
}


def _humanize_key(key: str) -> str:
    words = key.replace("_", " ").strip().split()
    return " ".join(_LABEL_OVERRIDES.get(word.lower(), word.capitalize()) for word in words)


def readable_text(value: Any) -> str:
    """Convert nested values to concise text for use inside custom HTML cards."""
    if isinstance(value, dict):
        return "; ".join(
            f"{_humanize_key(str(key))}: {readable_text(entry)}"
            for key, entry in value.items()
            if entry not in (None, "", [], {})
        ) or "No details provided"
    if isinstance(value, list):
        return ", ".join(readable_text(entry) for entry in value) or "No details provided"
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if value is None or value == "":
        return "Not provided"
    return str(value)


def safe_readable_text(value: Any) -> str:
    """Format and HTML-escape dynamic values embedded in custom cards."""
    return html.escape(readable_text(value))


def _parse_json_value(text: str) -> Any:
    candidate = text.strip()
    fenced = re.fullmatch(r"```(?:json)?\s*([\s\S]*?)\s*```", candidate, re.IGNORECASE)
    if fenced:
        candidate = fenced.group(1).strip()
    if candidate.startswith(("{", "[")):
        try:
            parsed_value = json.loads(candidate)
        except json.JSONDecodeError:
            return clean_markdown_json(candidate)
        if isinstance(parsed_value, (dict, list)):
            return parsed_value
    array_match = re.search(r"(\[[\s\S]*\])", candidate)
    if array_match:
        try:
            parsed_value = json.loads(array_match.group(1))
        except json.JSONDecodeError:
            parsed_value = None
        if isinstance(parsed_value, list):
            return parsed_value
    return clean_markdown_json(text)


def _render_value(label: str, value: Any) -> None:
    if value is None or value == "":
        return

    if isinstance(value, str):
        candidate = value.strip()
        if candidate.startswith(("{", "[", "```json")):
            parsed_value = _parse_json_value(candidate)
            if isinstance(parsed_value, (dict, list)):
                _render_value(label, parsed_value)
                return

    if isinstance(value, dict):
        st.markdown(f"#### {label}")
        render_readable_data(value)
        return

    if isinstance(value, list):
        st.markdown(f"#### {label}")
        if not value:
            st.caption("No details provided.")
        elif all(isinstance(item, dict) for item in value):
            for index, item in enumerate(value, start=1):
                title_field = next(
                    (field for field in ("name", "tier_name", "channel", "risk", "title") if item.get(field)),
                    None,
                )
                title = str(item[title_field]) if title_field else f"{label} {index}"
                with st.container(border=True):
                    st.markdown(f"**{title}**")
                    render_readable_data({key: entry for key, entry in item.items() if key != title_field})
        else:
            for item in value:
                if isinstance(item, (dict, list)):
                    render_readable_data({"Details": item})
                else:
                    st.markdown(f"- {item}")
        return

    if isinstance(value, bool):
        display_value = "Yes" if value else "No"
    elif isinstance(value, float) and value.is_integer():
        display_value = f"{int(value):,}"
    elif isinstance(value, (int, float)):
        display_value = f"{value:,}"
    else:
        display_value = str(value)

    if "score" in label.lower() and isinstance(value, (int, float)):
        st.metric(label, f"{display_value}/100")
    elif label.lower() == "summary":
        st.info(display_value)
    else:
        st.markdown(f"**{label}**")
        st.write(display_value)


def render_readable_data(data: Any) -> None:
    """Render nested dictionaries and lists as labeled sections instead of raw JSON."""
    if isinstance(data, dict):
        if not data:
            st.caption("No structured details are available.")
            return
        for key, value in data.items():
            _render_value(_humanize_key(str(key)), value)
    elif isinstance(data, list):
        _render_value("Details", data)
    else:
        st.write(data)


def render_agent_output(structured_output: Any, raw_output: str) -> None:
    """Render agent content without exposing JSON text as an unreadable fallback."""
    parsed_output = structured_output if structured_output not in ({}, []) else None
    if isinstance(parsed_output, str):
        parsed_output = _parse_json_value(parsed_output)

    if not isinstance(parsed_output, (dict, list)) and raw_output:
        parsed_output = _parse_json_value(raw_output)

    if isinstance(parsed_output, (dict, list)):
        render_readable_data(parsed_output)
        return

    if raw_output:
        raw_text = raw_output.strip()
        if raw_text.startswith(("{", "[")) or re.match(r"^```(?:json)?\s*[\[{]", raw_text, re.IGNORECASE):
            st.warning(
                "The agent returned structured data that could not be formatted. "
                "Please rerun the analysis to generate a readable result."
            )
        else:
            st.markdown(raw_text)
        return

    st.caption("No readable output is available for this agent yet.")


def render_additional_data(
    data: Any,
    displayed_keys: set[str],
    section_title: str,
) -> None:
    """Show structured fields not already presented by a page's tailored visuals."""
    if not isinstance(data, dict):
        return

    displayed = {key.lower() for key in displayed_keys}
    additional = {
        key: value
        for key, value in data.items()
        if key.lower() not in displayed and value not in (None, "", [], {})
    }
    if additional:
        with st.expander(section_title):
            render_readable_data(additional)
