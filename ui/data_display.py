"""Human-readable rendering helpers for structured agent and application data."""
from typing import Any

import streamlit as st


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


def _render_value(label: str, value: Any) -> None:
    if value is None or value == "":
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
