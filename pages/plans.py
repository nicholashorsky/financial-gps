"""ProjectionLab-inspired, clean-room planning workspace."""

from __future__ import annotations

from copy import deepcopy
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from shared.db import get_connection
from shared.planning_service import (
    REFRESHABLE_SECTIONS,
    archive_plan,
    create_plan,
    duplicate_plan,
    list_plans,
    project_plan,
    refresh_plan_sections,
    rename_plan,
    save_plan_revision,
    set_active_plan,
    snapshot_current_finances,
)
from shared.theme import PRIMARY, PRIMARY_LIGHT, style_figure
from shared.ui import page_header


def _money(value: float) -> str:
    return f"${value:,.0f}"


def _records(frame: pd.DataFrame) -> list[dict]:
    return [
        {key: (None if pd.isna(value) else value) for key, value in row.items()}
        for row in frame.to_dict(orient="records")
    ]


def _projection_frame(plan: dict) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Year": year.year,
                "Age": year.age,
                "Employment": year.employment_income,
                "CPP": year.cpp_received,
                "OAS": year.oas_received,
                "GIS": year.gis_received,
                "Taxable income": year.taxable_income,
                "Federal tax": year.federal_tax,
                "Provincial tax": year.provincial_tax,
                "OAS recovery": year.oas_recovery_tax,
                "Withdrawals": sum(year.withdrawals.values()),
                "RRIF minimum": year.rrif_minimum_withdrawal,
                "Spending": year.total_spending,
                "Surplus": year.net_surplus,
                "Net worth": year.net_worth,
                "Tax parameters": year.parameter_year,
                "Fallback": year.uses_parameter_fallback,
            }
            for year in project_plan(plan["payload"])
        ]
    )


def _render_plan_cards(conn, user_id: int, plans: list[dict]) -> None:
    st.subheader("Your Plans")
    for start in range(0, len(plans), 3):
        columns = st.columns(min(3, len(plans) - start))
        for column, plan in zip(columns, plans[start : start + 3], strict=False):
            with column:
                with st.container(border=True):
                    st.markdown(f"### {plan['name']}")
                    st.caption(
                        f"Revision {plan['revision_number']} · "
                        f"{'Active plan' if plan['is_active'] else 'Alternative'}"
                    )
                    projection = _projection_frame(plan)
                    if projection.empty:
                        st.info("Complete setup to generate a projection.")
                    else:
                        st.metric("Ending net worth", _money(float(projection.iloc[-1]["Net worth"])))
                        st.line_chart(
                            projection.set_index("Year")[["Net worth"]],
                            height=120,
                        )
                    if st.button(
                        "Open plan",
                        key=f"open_plan_{plan['id']}",
                        type="primary" if plan["is_active"] else "secondary",
                        use_container_width=True,
                    ):
                        set_active_plan(conn, user_id, plan["id"])
                        st.rerun()


def _save_payload(conn, user_id: int, plan: dict, payload: dict, reason: str) -> None:
    save_plan_revision(conn, user_id, plan["id"], payload, reason=reason)
    st.success("Plan updated.")
    st.rerun()


def _render_setup(conn, user_id: int, plan: dict) -> None:
    payload = plan["payload"]
    tabs = st.tabs(
        [
            "1. About You",
            "2. Income & Benefits",
            "3. Spending",
            "4. Accounts & Room",
            "5. Goal & Assumptions",
            "6. Review",
        ]
    )

    with tabs[0]:
        profile = payload["profile"]
        with st.form(f"about_{plan['id']}"):
            province_options = ["", "ON", "BC", "AB", "QC"]
            province = st.selectbox(
                "Province",
                province_options,
                index=province_options.index(profile.get("province") or ""),
            )
            saved_dob = profile.get("date_of_birth")
            dob = st.date_input(
                "Date of birth",
                value=date.fromisoformat(saved_dob) if saved_dob else date(1990, 1, 1),
                min_value=date(1900, 1, 1),
                max_value=date.today(),
            )
            resident = st.checkbox(
                "Currently resident in Canada",
                value=bool(profile.get("is_canadian_resident", True)),
            )
            years = st.number_input(
                "Years lived in Canada since age 18",
                min_value=0,
                max_value=60,
                value=int(profile.get("years_in_canada_post_18") or 40),
            )
            if st.form_submit_button("Save About You", type="primary"):
                updated = deepcopy(payload)
                updated["profile"].update(
                    {
                        "province": province or None,
                        "date_of_birth": dob.isoformat(),
                        "is_canadian_resident": resident,
                        "years_in_canada_post_18": years,
                        "is_quebec": province == "QC",
                    }
                )
                _save_payload(conn, user_id, plan, updated, "about")

    with tabs[1]:
        st.caption("Amounts are annual unless the benefit field says monthly.")
        income_columns = [
            "source_type",
            "annual_amount",
            "income_character",
            "start_year",
            "end_year",
            "inflation_rate",
            "is_pensionable",
        ]
        income_frame = pd.DataFrame(payload["income"], columns=income_columns)
        edited_income = st.data_editor(
            income_frame,
            num_rows="dynamic",
            use_container_width=True,
            key=f"income_editor_{plan['id']}_{plan['revision_number']}",
        )
        benefit_map = {row["benefit_type"].upper(): row for row in payload["benefits"]}
        with st.form(f"benefits_{plan['id']}"):
            left, right = st.columns(2)
            cpp = benefit_map.get("CPP", {})
            oas = benefit_map.get("OAS", {})
            cpp_age = left.slider("CPP start age", 60, 70, int(cpp.get("elected_start_age") or 65))
            cpp_amount = left.number_input(
                "CPP monthly estimate",
                min_value=0.0,
                value=float(cpp.get("estimated_monthly_amount") or 0),
            )
            oas_age = right.slider("OAS start age", 65, 70, int(oas.get("elected_start_age") or 65))
            if st.form_submit_button("Save Income & Benefits", type="primary"):
                updated = deepcopy(payload)
                updated["income"] = _records(edited_income)
                updated["benefits"] = [
                    {
                        "benefit_type": "CPP",
                        "elected_start_age": cpp_age,
                        "estimated_monthly_amount": cpp_amount or None,
                        "source": "manual" if cpp_amount else "calculated",
                        "cpp_estimate_at_65": cpp_amount or None,
                        "oas_years_resident": int(updated["profile"].get("years_in_canada_post_18") or 40),
                    },
                    {
                        "benefit_type": "OAS",
                        "elected_start_age": oas_age,
                        "estimated_monthly_amount": None,
                        "source": "calculated",
                        "oas_years_resident": int(updated["profile"].get("years_in_canada_post_18") or 40),
                    },
                ]
                _save_payload(conn, user_id, plan, updated, "income_benefits")

    with tabs[2]:
        spending_frame = pd.DataFrame(
            payload["spending"],
            columns=["category", "monthly_amount", "inflation_rate", "is_essential"],
        )
        edited_spending = st.data_editor(
            spending_frame,
            num_rows="dynamic",
            use_container_width=True,
            key=f"spending_editor_{plan['id']}_{plan['revision_number']}",
        )
        if st.button("Save Spending", type="primary", key=f"save_spending_{plan['id']}"):
            updated = deepcopy(payload)
            updated["spending"] = _records(edited_spending)
            _save_payload(conn, user_id, plan, updated, "spending")

    with tabs[3]:
        account_frame = pd.DataFrame(
            payload["accounts"],
            columns=["account_type", "current_balance", "opened_date", "institution", "beneficiary_type"],
        )
        edited_accounts = st.data_editor(
            account_frame,
            num_rows="dynamic",
            use_container_width=True,
            key=f"account_editor_{plan['id']}_{plan['revision_number']}",
        )
        room = payload["room"]
        room_rows = [
            {"Account": "TFSA", "Available room": room.get("tfsa", {}).get("available_room", 0)},
            {"Account": "RRSP", "Available room": room.get("rrsp", {}).get("deduction_limit", 0)},
            {"Account": "FHSA", "Available room": room.get("fhsa", {}).get("carryforward_room", 0)},
        ]
        st.dataframe(pd.DataFrame(room_rows), use_container_width=True, hide_index=True)
        if st.button("Save Accounts", type="primary", key=f"save_accounts_{plan['id']}"):
            updated = deepcopy(payload)
            updated["accounts"] = _records(edited_accounts)
            _save_payload(conn, user_id, plan, updated, "accounts")

    with tabs[4]:
        profile = payload["profile"]
        assumptions = payload["assumptions"]
        with st.form(f"goal_{plan['id']}"):
            target_year = st.number_input(
                "Target retirement year",
                min_value=date.today().year,
                max_value=date.today().year + 60,
                value=int(profile.get("target_retire_year") or date.today().year + 15),
            )
            spending_floor = st.number_input(
                "Annual retirement spending target",
                min_value=0.0,
                value=float(profile.get("spending_floor") or 50000),
                step=1000.0,
            )
            horizon = st.slider(
                "Projection horizon",
                min_value=10,
                max_value=80,
                value=int(assumptions.get("projection_years") or 40),
            )
            inflation = st.slider(
                "Spending inflation",
                min_value=0.0,
                max_value=0.08,
                value=float(assumptions.get("spending_inflation") or 0.025),
                step=0.005,
                format="%.1f%%",
            )
            if st.form_submit_button("Save Goal & Assumptions", type="primary"):
                updated = deepcopy(payload)
                updated["profile"]["target_retire_year"] = target_year
                updated["profile"]["spending_floor"] = spending_floor
                updated["assumptions"]["projection_years"] = horizon
                updated["assumptions"]["spending_inflation"] = inflation
                _save_payload(conn, user_id, plan, updated, "goal_assumptions")

    with tabs[5]:
        projection = _projection_frame(plan)
        completeness = {
            "About you": bool(payload["profile"].get("province") and payload["profile"].get("date_of_birth")),
            "Income": bool(payload["income"]),
            "Spending": bool(payload["spending"]),
            "Accounts": bool(payload["accounts"]),
            "Benefits": bool(payload["benefits"]),
        }
        st.dataframe(
            pd.DataFrame(
                [{"Section": name, "Ready": "Yes" if ready else "Needs attention"} for name, ready in completeness.items()]
            ),
            use_container_width=True,
            hide_index=True,
        )
        if projection.empty:
            st.warning("Complete About You before running this plan.")
        else:
            st.success("This plan is ready to project.")


def _render_projection(plan: dict, frame: pd.DataFrame) -> None:
    if frame.empty:
        st.warning("Complete the plan setup to generate a projection.")
        return
    profile = plan["payload"]["profile"]
    target_year = int(profile.get("target_retire_year") or frame.iloc[0]["Year"])
    target_row = frame.iloc[(frame["Year"] - target_year).abs().argsort()[:1]]
    metrics = st.columns(3)
    metrics[0].metric("Starting net worth", _money(float(frame.iloc[0]["Net worth"])))
    metrics[1].metric("At target year", _money(float(target_row.iloc[0]["Net worth"])))
    metrics[2].metric("Ending net worth", _money(float(frame.iloc[-1]["Net worth"])))
    chart = go.Figure()
    chart.add_trace(
        go.Scatter(
            x=frame["Year"],
            y=frame["Net worth"],
            mode="lines",
            name=plan["name"],
            line_color=PRIMARY,
        )
    )
    chart.add_vline(x=target_year, line_dash="dot", line_color=PRIMARY_LIGHT)
    style_figure(chart, height=430)
    chart.update_layout(yaxis_title="Net worth")
    st.plotly_chart(chart, use_container_width=True)
    st.caption(
        f"Deterministic {len(frame)}-year projection · "
        f"{float(plan['payload']['assumptions']['spending_inflation']):.1%} spending inflation"
    )


def _render_compare(plans: list[dict], active_plan: dict) -> None:
    options = {plan["name"]: plan for plan in plans}
    default_names = [active_plan["name"]] + [name for name in options if name != active_plan["name"]][:2]
    selected = st.multiselect(
        "Compare up to three plans",
        options=list(options),
        default=default_names,
        max_selections=3,
    )
    if len(selected) < 2:
        st.info("Select at least two plans to compare.")
        return
    chart = go.Figure()
    outcomes = []
    for name in selected:
        frame = _projection_frame(options[name])
        if frame.empty:
            st.warning(f"{name} needs more setup before it can be compared.")
            continue
        chart.add_trace(go.Scatter(x=frame["Year"], y=frame["Net worth"], mode="lines", name=name))
        outcomes.append(
            {
                "Plan": name,
                "Starting net worth": frame.iloc[0]["Net worth"],
                "Ending net worth": frame.iloc[-1]["Net worth"],
                "First-year surplus": frame.iloc[0]["Surplus"],
            }
        )
    style_figure(chart, height=420)
    st.plotly_chart(chart, use_container_width=True)
    st.dataframe(pd.DataFrame(outcomes), use_container_width=True, hide_index=True)


def _render_settings(conn, user_id: int, plan: dict) -> None:
    st.subheader("Plan Settings")
    with st.form(f"rename_{plan['id']}"):
        name = st.text_input("Plan name", value=plan["name"])
        if st.form_submit_button("Rename plan"):
            rename_plan(conn, user_id, plan["id"], name)
            st.success("Plan renamed.")
            st.rerun()

    if st.button("Duplicate plan", key=f"duplicate_{plan['id']}"):
        duplicate_plan(conn, user_id, plan["id"])
        st.success("Plan duplicated.")
        st.rerun()

    st.divider()
    st.subheader("Refresh from current finances")
    current = snapshot_current_finances(conn, user_id)
    rows = []
    for section in sorted(REFRESHABLE_SECTIONS):
        planned = plan["payload"][section]
        source = current[section]
        rows.append(
            {
                "Section": section.title(),
                "Plan records": len(planned) if isinstance(planned, list) else "Snapshot",
                "Current records": len(source) if isinstance(source, list) else "Snapshot",
                "Last refreshed": plan["payload"]["provenance"]["sections"].get(section, "Never"),
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    selected = {
        section
        for section in sorted(REFRESHABLE_SECTIONS)
        if st.checkbox(section.title(), key=f"refresh_{plan['id']}_{section}")
    }
    if selected:
        with st.expander("Review selected changes", expanded=True):
            before, after = st.columns(2)
            with before:
                st.markdown("**Plan now**")
                st.json({section: plan["payload"][section] for section in sorted(selected)})
            with after:
                st.markdown("**After refresh**")
                st.json({section: current[section] for section in sorted(selected)})
    st.warning("Refreshing replaces only the selected plan sections. It never changes current finances.")
    if st.button(
        "Confirm selected refresh",
        disabled=not selected,
        key=f"confirm_refresh_{plan['id']}",
    ):
        refresh_plan_sections(conn, user_id, plan["id"], selected)
        st.success("Selected sections refreshed.")
        st.rerun()

    st.divider()
    st.caption(
        f"Revision {plan['revision_number']} · Source: "
        f"{plan['payload']['provenance'].get('source', 'manual')}"
    )
    with st.expander("Archive plan"):
        st.warning("Archived plans are hidden from the active workspace but their revisions remain stored.")
        if st.button("Archive this plan", key=f"archive_{plan['id']}"):
            archive_plan(conn, user_id, plan["id"])
            st.rerun()


def render() -> None:
    page_header(
        "Plans",
        "Build independent Canadian financial plans, inspect the cash flow, and compare possible paths.",
    )
    user = st.session_state.get("user")
    if not user:
        st.info("Log in to build plans.")
        return
    user_id = int(user["id"])
    conn = get_connection()
    try:
        plans = list_plans(conn, user_id)
        with st.expander("Create a plan", expanded=not plans):
            with st.form("create_planning_plan"):
                name = st.text_input("Plan name", value="My Plan")
                source = st.radio(
                    "Starting point",
                    ["Current finances snapshot", "Blank plan"],
                    horizontal=True,
                )
                if st.form_submit_button("Create plan", type="primary"):
                    create_plan(
                        conn,
                        user_id,
                        name,
                        from_current_finances=source == "Current finances snapshot",
                    )
                    st.success("Plan created.")
                    st.rerun()

        if not plans:
            st.info("Create your first plan to begin.")
            return

        _render_plan_cards(conn, user_id, plans)
        active = next((plan for plan in plans if plan["is_active"]), plans[0])
        st.divider()
        st.markdown(f"## {active['name']}")
        tabs = st.tabs(["Projection", "Setup", "Cash Flow", "Tax & Benefits", "Compare", "Settings"])
        frame = _projection_frame(active)
        with tabs[0]:
            _render_projection(active, frame)
        with tabs[1]:
            _render_setup(conn, user_id, active)
        with tabs[2]:
            if frame.empty:
                st.info("Complete setup to view cash flow.")
            else:
                st.dataframe(
                    frame[
                        [
                            "Year",
                            "Age",
                            "Employment",
                            "CPP",
                            "OAS",
                            "GIS",
                            "Withdrawals",
                            "Spending",
                            "Surplus",
                            "Net worth",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
        with tabs[3]:
            if frame.empty:
                st.info("Complete setup to view taxes and benefits.")
            else:
                st.dataframe(
                    frame[
                        [
                            "Year",
                            "Taxable income",
                            "Federal tax",
                            "Provincial tax",
                            "OAS recovery",
                            "CPP",
                            "OAS",
                            "GIS",
                            "RRIF minimum",
                            "Tax parameters",
                            "Fallback",
                        ]
                    ],
                    use_container_width=True,
                    hide_index=True,
                )
                if frame["Fallback"].any():
                    st.info("Years without verified CRA parameters use the documented 2026 fallback.")
        with tabs[4]:
            _render_compare(plans, active)
        with tabs[5]:
            _render_settings(conn, user_id, active)
    finally:
        conn.close()
