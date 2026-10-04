"""
Sidebar navigation component.
Renders navigation items, active startup selector, token budget indicator, and founder profile.
"""
from typing import Optional, List
from pathlib import Path
import streamlit as st
from utils.constants import NAV_ITEMS, APP_NAME
from database.models import Startup
from config.llm_config import global_token_manager, get_llm_config
from rag.faiss_manager import faiss_manager
from ui.styles import render_html, get_width_kwargs


def _set_current_page(page: str) -> None:
    """Persist a sidebar navigation button selection before the app reruns."""
    st.session_state["current_page"] = page


def render_sidebar(startups: List[Startup], active_startup: Optional[Startup]) -> str:
    """
    Renders the dark sidebar and returns the currently selected page key.
    """
    with st.sidebar:
        # 1. Branding Header
        logo_col, brand_col = st.columns([0.9, 3.4], gap="small")
        with logo_col:
            logo_path = Path(__file__).resolve().parents[1] / "assets" / "venture_logo.svg"
            st.image(logo_path.read_text(encoding="utf-8"), width=46)
        with brand_col:
            render_html(
                f"""
                <div style="padding: 5px 0 0 0;">
                    <div style="font-weight: 750; font-size: 0.98rem; color: #FFFFFF; letter-spacing: -0.025em;">
                        {APP_NAME}
                    </div>
                    <div style="font-size: 0.72rem; color: #94A3B8; font-weight: 500; margin-top: 3px;">
                        AI Founding Suite
                    </div>
                </div>
                """
            )
        render_html("<div style='height: 14px;'></div>")

        # 2. Startup Selector (if startups exist)
        if startups:
            options = {s.id: f"{s.name} ({s.country})" for s in startups}
            current_id = active_startup.id if active_startup else startups[0].id
            default_index = (
                list(options.keys()).index(current_id)
                if current_id in options
                else 0
            )

            selected_id = st.selectbox(
                "Active Startup",
                options=list(options.keys()),
                format_func=lambda x: options[x],
                index=default_index,
                label_visibility="collapsed",
            )
            if selected_id != current_id:
                st.session_state["selected_startup_id"] = selected_id
                st.rerun()

        render_html("<div style='height: 8px;'></div>")

        # 3. Navigation List
        if "current_page" not in st.session_state:
            st.session_state["current_page"] = "Overview"

        nav_labels = [item[0] for item in NAV_ITEMS]
        current_nav = st.session_state["current_page"]
        if current_nav not in nav_labels:
            current_nav = nav_labels[0]
            st.session_state["current_page"] = current_nav

        # Use buttons instead of radio controls for a more polished, direct navigation.
        for label, icon in NAV_ITEMS:
            st.button(
                f"{icon}  {label}",
                key=f"nav_{label.lower().replace(' ', '_')}",
                type="primary" if label == current_nav else "secondary",
                on_click=_set_current_page,
                args=(label,),
                **get_width_kwargs(True),
            )

        render_html("<div style='height: 24px;'></div>")

        # 4. Token Budget Status (Global 7,500 token tracker)
        budget_summary = global_token_manager.get_summary()
        used = budget_summary["total_used"]
        total = budget_summary["max_total_tokens"]
        pct = budget_summary["usage_percent"]

        render_html(
            f"""
            <div style="background: #111726; border: 1px solid #1E293B; border-radius: 8px; padding: 10px; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; font-size: 0.72rem; color: #94A3B8; margin-bottom: 4px;">
                    <span>OUTPUT TOKEN BUDGET</span>
                    <span style="color: #6366F1; font-weight: 600;">{used:,} / {total:,}</span>
                </div>
                <div style="background: #1E293B; border-radius: 4px; height: 5px; width: 100%; overflow: hidden;">
                    <div style="background: #6366F1; height: 100%; width: {min(100, pct)}%;"></div>
                </div>
            </div>
            """
        )

        # 5. Founder Profile at Sidebar Footer
        founder_name = (
            "Malik Kashan"
            if (not active_startup or not active_startup.founder_name or active_startup.founder_name in ["Ali Hassan", "Ahmed Khan", "Founder"])
            else active_startup.founder_name
        )
        render_html(
            f"""
            <div style="margin-top: auto; padding-top: 16px; border-top: 1px solid #1E293B; display: flex; align-items: center; gap: 10px;">
                <div style="background: #3B82F6; width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.85rem; color: #FFFFFF;">
                    {founder_name[0] if founder_name else 'F'}
                </div>
                <div style="line-height: 1.2;">
                    <div style="font-size: 0.85rem; font-weight: 600; color: #FFFFFF;">
                        {founder_name}
                    </div>
                    <div style="font-size: 0.72rem; color: #94A3B8;">
                        Founder
                    </div>
                </div>
            </div>
            <div style="padding-top: 8px; font-size: 0.7rem; color: #64748B;">
                Developed by Malik Kashan
            </div>
            """
        )

        return st.session_state["current_page"]
