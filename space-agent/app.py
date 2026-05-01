"""Streamlit GUI for Systems Engineering AI Agent."""

from __future__ import annotations

import asyncio
from datetime import date
from pathlib import Path

import streamlit as st

from assembler.pdf_builder import build_pdf_proposal
from config import ConfigError, OUTPUTS_DIR, require_api_key
from coordinator import Coordinator
from schemas.output_schemas import MissionContext
from utils.deployment_utils import (
    MAX_GENERATIONS_PER_SESSION,
    generation_limit_reached,
    get_app_password,
    has_demo_password,
    is_production_mode,
    sanitize_mission_name,
    verify_password,
)
from utils.mission_context_adapter import (
    build_agent_mission_context,
    payload_details_quality_warning,
    validate_gui_mission_context,
)


st.set_page_config(page_title="Systems Engineering AI Agent", layout="wide")

SAMPLE_GUI_CONTEXT = {
    "mission_name": "AlpineWatch-1",
    "mission_type": "Earth Observation Mission",
    "altitude_km": 550.0,
    "inclination_deg": 97.6,
    "lifetime_years": 3.0,
    "payload_details": (
        "Multispectral Earth Observation payload with 40 km swath width, 5 m GSD, "
        "8 kg payload mass, and 35 W nominal power consumption."
    ),
    "mission_scope": "single_satellite",
    "payload_type": "earth_observation",
}

DEFAULTS = {
    "mission_name": "AlpineWatch-1",
    "mission_type": "Earth Observation Mission",
    "altitude_km": 550.0,
    "inclination_deg": 97.6,
    "lifetime_years": 3.0,
    "payload_details": SAMPLE_GUI_CONTEXT["payload_details"],
    "parsed_mission_context": None,
    "agent_mission_context": None,
    "agent_outputs": None,
    "generated_pdf_path": None,
    "generated_docx_path": None,
    "warnings": [],
    "progress_tracker": None,
    "pipeline_failures": [],
    "authenticated": False,
    "generation_count": 0,
    "is_generating": False,
}


def init_state() -> None:
    for key, value in DEFAULTS.items():
        st.session_state.setdefault(key, value)


def inject_css() -> None:
    st.markdown(
        """
<style>
.stApp { background: #0b1220; color: #e6edf7; }
.hero-card, .input-card, .summary-card, .info-card, .metric-card, .step-card, .footer {
  background: #111a2e;
  border: 1px solid #25314b;
  border-radius: 14px;
  padding: 14px 16px;
}
.hero-title { font-size: 2rem; font-weight: 700; margin: 0 0 4px 0; }
.hero-subtitle { color: #9eb0cf; margin: 0 0 12px 0; }
.feature-badge {
  display: inline-block;
  font-size: 0.82rem;
  font-weight: 600;
  background: #1a2844;
  color: #d5e2fb;
  border: 1px solid #324a78;
  border-radius: 999px;
  padding: 4px 10px;
  margin-right: 8px;
}
.card-title { font-size: 1.05rem; font-weight: 650; margin: 0 0 8px 0; }
.muted { color: #9eb0cf; font-size: 0.9rem; }
.ready { color: #49d17d; font-weight: 700; }
.needs { color: #f2c96a; font-weight: 700; }
.step-label { font-weight: 600; }
.step-waiting { color: #9eb0cf; }
.step-running { color: #7dc4ff; }
.step-complete { color: #49d17d; }
.step-failed { color: #ff8b8b; }
</style>
""",
        unsafe_allow_html=True,
    )


def render_sidebar_security() -> None:
    st.sidebar.markdown("### Security")
    if has_demo_password():
        st.sidebar.success("Demo access protection is enabled.")
    else:
        st.sidebar.warning(
            "Demo access protection is disabled. Set APP_PASSWORD before public deployment."
        )


def enforce_access_gate() -> None:
    app_password = get_app_password()
    if not app_password:
        st.session_state["authenticated"] = True
        return
    if st.session_state.get("authenticated"):
        return

    st.markdown("### Demo Access")
    entered = st.text_input("Enter demo password", type="password", key="app_password_input")
    if st.button("Unlock App", use_container_width=True):
        if verify_password(entered, app_password):
            st.session_state["authenticated"] = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    st.stop()


def render_hero() -> None:
    st.markdown(
        """
<div class="hero-card">
  <div class="hero-title">Systems Engineering AI Agent</div>
  <div class="hero-subtitle">Generate editable Phase 0 spacecraft mission proposal drafts from structured mission concepts.</div>
  <span class="feature-badge">Mission Requirements</span>
  <span class="feature-badge">Mass &amp; Power Budgets</span>
  <span class="feature-badge">Editable DOCX Export</span>
</div>
""",
        unsafe_allow_html=True,
    )


def render_scope_notice() -> None:
    st.markdown(
        """
<div class="info-card">
  <div class="card-title">MVP Scope Notice</div>
  <div class="muted">This MVP supports single-satellite Earth Observation concepts. Constellation design, multi-plane phasing, revisit optimization, and non-EO payloads are planned future extensions.</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_input_form() -> dict:
    st.markdown('<div class="input-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-title">Mission Input Card</div>', unsafe_allow_html=True)

    mission_name = st.text_input("Mission name *", key="mission_name", max_chars=80)
    mission_type = st.text_input("Mission type *", key="mission_type", max_chars=80)
    st.caption("For now only EO missions are possible. Future versions will expand to other mission types.")
    altitude_km = st.number_input("Altitude [km] *", min_value=100.0, max_value=2000.0, value=st.session_state["altitude_km"])
    inclination_deg = st.number_input("Inclination [deg] *", min_value=0.0, max_value=180.0, value=st.session_state["inclination_deg"])
    lifetime_years = st.number_input("Lifetime [years] *", min_value=0.1, max_value=15.0, value=st.session_state["lifetime_years"])
    payload_details = st.text_area(
        "Payload details *",
        value=st.session_state["payload_details"],
        height=110,
        max_chars=3000,
        placeholder=(
            "Example: Multispectral Earth Observation payload with 40 km swath width, 5 m GSD, "
            "8 kg payload mass, and 35 W nominal power consumption."
        ),
    )

    generate_clicked = st.button("Generate Proposal", type="primary", use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

    return {
        "mission_name": mission_name,
        "mission_type": mission_type,
        "altitude_km": altitude_km,
        "inclination_deg": inclination_deg,
        "lifetime_years": lifetime_years,
        "payload_details": payload_details,
        "generate_clicked": generate_clicked,
    }


def render_progress_tracker(tracker: dict[str, str] | None) -> None:
    if not tracker:
        return
    st.markdown('<div class="card-title">Pipeline Progress</div>', unsafe_allow_html=True)
    total = len(tracker)
    complete = sum(1 for status in tracker.values() if status == "Complete")
    st.progress(complete / total if total else 0.0)
    st.caption(f"{complete}/{total} steps complete")
    cols = st.columns(3)
    steps = list(tracker.items())
    for idx, (name, status) in enumerate(steps):
        css = f"step-{status.lower()}"
        icon = {
            "Waiting": "⏳",
            "Running": "🔄",
            "Complete": "✅",
            "Failed": "❌",
        }.get(status, "•")
        with cols[idx % 3]:
            st.markdown(
                f"<div class='step-card'><div class='step-label'>{icon} {name}</div><div class='{css}'>{status}</div></div>",
                unsafe_allow_html=True,
            )


def render_results_tabs(outputs: dict, gui_ctx: dict | None, agent_ctx: dict | None) -> None:
    tabs = st.tabs(["Overview", "Requirements", "Mass", "Power", "Cost", "Procurement", "Export"])

    mission = outputs.get("mission", {})
    mass = outputs.get("mass", {})
    power = outputs.get("power", {})
    cost = outputs.get("cost", {})
    procurement = outputs.get("procurement", {})

    with tabs[0]:
        if gui_ctx:
            st.markdown("**Mission Inputs**")
            st.dataframe(
                [
                    ["Mission name", gui_ctx.get("mission_name", "")],
                    ["Mission type", gui_ctx.get("mission_type", "")],
                    ["Altitude [km]", gui_ctx.get("altitude_km", "")],
                    ["Inclination [deg]", gui_ctx.get("inclination_deg", "")],
                    ["Lifetime [years]", gui_ctx.get("lifetime_years", "")],
                    ["Payload details", gui_ctx.get("payload_details", "")],
                ],
                hide_index=True,
                use_container_width=True,
            )
        if agent_ctx:
            st.markdown("**Derived Agent Context**")
            st.dataframe(
                [
                    ["orbit", agent_ctx.get("orbit", "")],
                    ["payload_description", agent_ctx.get("payload_description", "")],
                    ["launch_vehicle", agent_ctx.get("launch_vehicle", "")],
                ],
                hide_index=True,
                use_container_width=True,
            )
        st.markdown("**Mission Overview**")
        for objective in mission.get("objectives", []):
            st.write(f"- {objective}")
        st.write(mission.get("conops_summary", ""))

    with tabs[1]:
        st.dataframe(
            mission.get("requirements", []),
            column_config={
                "id": "ID",
                "text": "Requirement",
                "rationale": "Rationale",
            },
            use_container_width=True,
            hide_index=True,
        )

    with tabs[2]:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total dry mass [kg]", f"{mass.get('total_dry_mass_kg', 0):.2f}")
        m2.metric("Total wet mass [kg]", f"{mass.get('total_wet_mass_kg', 0):.2f}")
        m3.metric("Margin [%]", f"{mass.get('mass_margin_pct', 0):.2f}")
        m4.metric("Status", mass.get("status", "UNKNOWN"))
        st.dataframe(mass.get("subsystems", []), use_container_width=True, hide_index=True)

    with tabs[3]:
        p1, p2, p3, p4, p5 = st.columns(5)
        p1.metric("Solar area [m²]", f"{power.get('solar_array_area_m2', 0):.2f}")
        p2.metric("Battery [Wh]", f"{power.get('battery_capacity_Wh', 0):.2f}")
        p3.metric("Eclipse [min]", f"{power.get('eclipse_duration_min', 0):.2f}")
        p4.metric("Margin [%]", f"{power.get('power_margin_pct', 0):.2f}")
        p5.metric("Status", power.get("status", "UNKNOWN"))
        mode_rows = []
        for mode_name, mode_data in power.get("modes", {}).items():
            mode_rows.append({"mode": mode_name, "total_W": mode_data.get("total_W", 0)})
        st.dataframe(mode_rows, use_container_width=True, hide_index=True)

    with tabs[4]:
        st.metric("Total cost [kEUR]", f"{cost.get('total_cost_kEUR', 0):.2f}")
        st.metric("Confidence", cost.get("confidence", "UNKNOWN"))
        st.dataframe(cost.get("cost_breakdown", []), use_container_width=True, hide_index=True)

    with tabs[5]:
        for search in procurement.get("component_searches", []):
            st.markdown(f"**Category: {search.get('category', '')}**")
            st.caption(search.get("requirement_basis", ""))
            st.dataframe(search.get("alternatives", []), use_container_width=True, hide_index=True)
            for warning in search.get("warnings", []):
                st.info(warning)

    with tabs[6]:
        docx_path = st.session_state.get("generated_docx_path")
        pdf_path = st.session_state.get("generated_pdf_path")

        st.markdown("### Primary Export")
        if docx_path and Path(docx_path).exists():
            st.download_button(
                "Download editable Word proposal (.docx)",
                data=Path(docx_path).read_bytes(),
                file_name=Path(docx_path).name,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                type="primary",
            )
            if is_production_mode():
                st.caption(f"Generated DOCX file: `{Path(docx_path).name}`")
            else:
                st.caption(f"Generated DOCX path: `{docx_path}`")
        st.caption("DOCX is the primary export format so the generated draft can be reviewed, edited, and corrected before use.")

        if pdf_path and Path(pdf_path).exists():
            st.markdown("### Optional Secondary Export")
            st.download_button(
                "Download optional PDF (.pdf)",
                data=Path(pdf_path).read_bytes(),
                file_name=Path(pdf_path).name,
                mime="application/pdf",
            )

        st.markdown(
            "**AI-assisted draft disclaimer:** This document is an AI-assisted Phase 0 concept draft. "
            "All technical values, cost estimates, procurement options, and requirements must be reviewed and "
            "validated by a qualified spacecraft systems engineer before use in design, procurement, proposal "
            "submission, or mission decision-making."
        )


def render_footer() -> None:
    st.markdown(
        f"""
<div class="footer muted">
  Systems Engineering AI Agent | MVP interface | {date.today().isoformat()}
</div>
""",
        unsafe_allow_html=True,
    )


def main() -> None:
    init_state()
    inject_css()
    render_sidebar_security()
    enforce_access_gate()
    try:
        require_api_key()
    except ConfigError:
        st.info(
            "OPENAI_API_KEY is not configured yet. Set it in local .env or in your deployment platform environment variables."
        )

    render_hero()
    render_scope_notice()

    left_col, right_col = st.columns([1.2, 1.0], gap="large")
    with left_col:
        inputs = render_input_form()

    if inputs["generate_clicked"]:
        if st.session_state.get("is_generating"):
            st.warning("Generation is already in progress.")
            return
        if generation_limit_reached(st.session_state.get("generation_count", 0)):
            st.error(
                "You have reached the demo generation limit for this session. Restart the session or run locally to continue."
            )
            return

        tracker = {
            "Mission Analysis": "Waiting",
            "Mass Budget": "Waiting",
            "Power Budget": "Waiting",
            "Cost Estimate": "Waiting",
            "Procurement Search": "Waiting",
            "Proposal Assembly": "Waiting",
        }
        st.session_state["progress_tracker"] = tracker
        st.session_state["is_generating"] = True
        live_progress = st.progress(0.0)
        live_status = st.empty()

        def _render_live_tracker() -> None:
            lines = []
            for step_name, status in tracker.items():
                icon = {
                    "Waiting": "⏳",
                    "Running": "🔄",
                    "Complete": "✅",
                    "Failed": "❌",
                }.get(status, "•")
                lines.append(f"- {icon} **{step_name}**: {status}")
            live_status.markdown("\n".join(lines))

        try:
            try:
                require_api_key()
            except ConfigError as exc:
                st.error(
                    f"Setup required: {exc} Set OPENAI_API_KEY in local .env or deployment environment variables."
                )
                st.session_state["is_generating"] = False
                return

            gui_context = {
                "mission_name": inputs["mission_name"],
                "mission_type": inputs["mission_type"],
                "altitude_km": inputs["altitude_km"],
                "inclination_deg": inputs["inclination_deg"],
                "lifetime_years": inputs["lifetime_years"],
                "payload_details": inputs["payload_details"],
                "mission_scope": "single_satellite",
                "payload_type": "earth_observation",
            }

            missing_fields = []
            if not str(gui_context["mission_name"]).strip():
                missing_fields.append("Mission name")
            if not str(gui_context["mission_type"]).strip():
                missing_fields.append("Mission type")
            if not str(gui_context["payload_details"]).strip():
                missing_fields.append("Payload details")
            if missing_fields:
                st.error(f"Please complete all required fields: {', '.join(missing_fields)}.")
                st.session_state["is_generating"] = False
                return

            validated_gui = validate_gui_mission_context(gui_context)
            warning = payload_details_quality_warning(validated_gui.payload_details)
            st.session_state["warnings"] = [warning] if warning else []

            agent_context_dict = build_agent_mission_context(validated_gui.model_dump())
            agent_context = MissionContext.model_validate(agent_context_dict)
            st.session_state["parsed_mission_context"] = validated_gui.model_dump()
            st.session_state["agent_mission_context"] = agent_context_dict

            old_docx = st.session_state.get("generated_docx_path")
            old_pdf = st.session_state.get("generated_pdf_path")
            for old in [old_docx, old_pdf]:
                if old and Path(old).exists():
                    try:
                        Path(old).unlink()
                    except OSError:
                        pass

            step_map = {
                "Mission analysis": "Mission Analysis",
                "Mass budget": "Mass Budget",
                "Power budget": "Power Budget",
                "Cost estimate": "Cost Estimate",
                "Procurement search": "Procurement Search",
                "Proposal assembly": "Proposal Assembly",
            }

            def on_progress(step: str, status: str) -> None:
                mapped = step_map.get(step, step)
                if mapped in tracker:
                    tracker[mapped] = "Running" if status == "running" else "Complete"
                    st.session_state["progress_tracker"] = tracker
                    complete = sum(1 for v in tracker.values() if v == "Complete")
                    live_progress.progress(complete / len(tracker))
                    _render_live_tracker()

            coordinator = Coordinator(auto_yes=True)
            run_result = asyncio.run(
                coordinator.run_with_outputs(agent_context, progress_callback=on_progress, build_docx=True)
            )

            st.session_state["agent_outputs"] = run_result["outputs"]
            st.session_state["generated_docx_path"] = str(run_result["docx_path"])
            st.session_state["pipeline_failures"] = run_result.get("failures", [])
            st.session_state["generation_count"] = st.session_state.get("generation_count", 0) + 1

            mission_safe = sanitize_mission_name(agent_context.mission_name)
            pdf_name = f"Phase_0_Proposal_{mission_safe}.pdf"
            pdf_path = OUTPUTS_DIR / pdf_name
            try:
                st.session_state["generated_pdf_path"] = build_pdf_proposal(run_result["outputs"], str(pdf_path))
            except Exception:
                st.session_state["generated_pdf_path"] = None

            for step in tracker:
                if tracker[step] != "Complete":
                    tracker[step] = "Complete"
            st.session_state["progress_tracker"] = tracker
            live_progress.progress(1.0)
            _render_live_tracker()
            st.success("Proposal generation complete.")

        except ConfigError as exc:
            tracker["Mission Analysis"] = "Failed"
            st.session_state["progress_tracker"] = tracker
            _render_live_tracker()
            st.error(f"Setup required: {exc} (see .env and OPENAI_API_KEY).")
        except TimeoutError:
            tracker["Mission Analysis"] = "Failed"
            st.session_state["progress_tracker"] = tracker
            _render_live_tracker()
            st.error("OpenAI request timed out. Please retry.")
        except ConnectionError:
            tracker["Mission Analysis"] = "Failed"
            st.session_state["progress_tracker"] = tracker
            _render_live_tracker()
            st.error("OpenAI connection failed. Check network or API availability, then retry.")
        except Exception as exc:
            failed_set = False
            for step_name, value in tracker.items():
                if value == "Running":
                    tracker[step_name] = "Failed"
                    failed_set = True
                    break
            if not failed_set:
                tracker["Mission Analysis"] = "Failed"
            st.session_state["progress_tracker"] = tracker
            _render_live_tracker()
            st.error(f"Generation failed: {exc}")
        finally:
            st.session_state["is_generating"] = False

    with right_col:
        st.markdown('<div class="summary-card">', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Output Parameters</div>', unsafe_allow_html=True)
        st.caption(
            f"Session generations used: {st.session_state.get('generation_count', 0)}/{MAX_GENERATIONS_PER_SESSION}"
        )

        if st.session_state.get("warnings"):
            for warning in st.session_state["warnings"]:
                st.info(warning)
        if st.session_state.get("pipeline_failures"):
            for failure in st.session_state["pipeline_failures"]:
                st.error(
                    f"Agent failure in '{failure.get('section', 'unknown')}': {failure.get('error', 'unknown error')}. "
                    "Fallback output was used for this section."
                )

        render_progress_tracker(st.session_state.get("progress_tracker"))

        outputs = st.session_state.get("agent_outputs")
        if outputs:
            if outputs.get("mass", {}).get("status") == "RED" or outputs.get("power", {}).get("status") == "RED":
                st.warning("Mass or Power status is RED. Review outputs before operational decisions.")

            render_results_tabs(
                outputs,
                st.session_state.get("parsed_mission_context"),
                st.session_state.get("agent_mission_context"),
            )
        else:
            st.caption("Generate a proposal to view output parameters and export options.")
        st.markdown('</div>', unsafe_allow_html=True)

    render_footer()


if __name__ == "__main__":
    main()
