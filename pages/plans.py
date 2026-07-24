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
    delete_plan,
    duplicate_plan,
    list_plans,
    project_plan,
    refresh_plan_sections,
    rename_plan,
    save_plan_revision,
    set_active_plan,
    snapshot_current_finances,
    spending_suggestions,
)
from shared.theme import PRIMARY, PRIMARY_LIGHT, style_figure
from shared.ui import page_header


def _money(value: float) -> str:
    return f"${value:,.0f}"


def _projection_frame(plan: dict) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Year": year.year,
                "Age": year.age,
                "Employment": year.employment_income,
                "Total income": (
                    year.employment_income
                    + year.cpp_received
                    + year.oas_received
                    + year.gis_received
                ),
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
                        st.session_state.planning_workspace_plan_id = plan["id"]
                        st.session_state.planning_edit_mode = False
                        st.rerun()


def _save_payload(conn, user_id: int, plan: dict, payload: dict, reason: str) -> None:
    save_plan_revision(conn, user_id, plan["id"], payload, reason=reason)
    st.success("Plan updated.")
    st.rerun()


def _render_income_inputs(conn, user_id: int, plan: dict) -> None:
    payload = plan["payload"]
    st.subheader("Income")
    st.caption("Add each source that should fund this plan.")
    with st.popover("＋ Add income", use_container_width=True):
        with st.form(f"add_income_{plan['id']}", clear_on_submit=True):
            source_type = st.selectbox(
                "Income type",
                ["Employment", "Pension", "Side hustle", "Rental", "Other"],
            )
            annual_amount = st.number_input("Annual amount", min_value=0.0, step=1000.0)
            growth = st.number_input("Annual growth %", min_value=-20.0, max_value=30.0, value=3.0)
            starts_later = st.checkbox("This income starts in a future year")
            start_year = st.number_input(
                "Future start year",
                min_value=date.today().year,
                value=date.today().year + 1,
                disabled=not starts_later,
            )
            has_end = st.checkbox("This income has an end year")
            end_year = st.number_input(
                "End year",
                min_value=date.today().year,
                value=date.today().year + 10,
                disabled=not has_end,
            )
            if st.form_submit_button("Add income", type="primary"):
                resolved_start = int(start_year) if starts_later else None
                resolved_end = int(end_year) if has_end else None
                if resolved_end and resolved_start and resolved_end < resolved_start:
                    st.error("End year must be the same as or later than the start year.")
                    return
                updated = deepcopy(payload)
                updated["income"].append(
                    {
                        "source_type": source_type.lower().replace(" ", "_"),
                        "annual_amount": annual_amount,
                        "income_character": "employment" if source_type == "Employment" else "other",
                        "start_year": resolved_start,
                        "end_year": resolved_end,
                        "inflation_rate": growth / 100,
                        "is_pensionable": source_type == "Employment",
                    }
                )
                _save_payload(conn, user_id, plan, updated, "income_added")

    if not payload["income"]:
        st.info("No income sources yet.")
    for index, income in enumerate(payload["income"]):
        label = str(income.get("source_type") or "Income").replace("_", " ").title()
        with st.expander(f"{label} · {_money(float(income.get('annual_amount') or 0))}/year"):
            with st.form(f"edit_income_{plan['id']}_{index}"):
                amount = st.number_input(
                    "Annual amount",
                    min_value=0.0,
                    value=float(income.get("annual_amount") or 0),
                    step=1000.0,
                )
                growth = st.number_input(
                    "Annual growth %",
                    min_value=-20.0,
                    max_value=30.0,
                    value=float(income.get("inflation_rate") or 0) * 100,
                    key=f"income_growth_{plan['id']}_{index}",
                )
                saved_start = income.get("start_year")
                saved_end = income.get("end_year")
                starts_later = st.checkbox(
                    "This income starts in a future year",
                    value=bool(saved_start and int(saved_start) > date.today().year),
                )
                start = st.number_input(
                    "Future start year",
                    min_value=date.today().year,
                    value=max(int(saved_start or date.today().year + 1), date.today().year),
                    disabled=not starts_later,
                )
                has_end = st.checkbox(
                    "This income has an end year",
                    value=saved_end is not None,
                )
                end = st.number_input(
                    "End year",
                    min_value=date.today().year,
                    value=max(int(saved_end or date.today().year + 10), date.today().year),
                    disabled=not has_end,
                )
                save_col, delete_col = st.columns(2)
                save = save_col.form_submit_button("Save income", type="primary")
                remove = delete_col.form_submit_button("Delete income")
                if save:
                    resolved_start = int(start) if starts_later else None
                    resolved_end = int(end) if has_end else None
                    if resolved_end and resolved_start and resolved_end < resolved_start:
                        st.error("End year must be the same as or later than the start year.")
                        return
                    updated = deepcopy(payload)
                    updated["income"][index].update(
                        {
                            "annual_amount": amount,
                            "inflation_rate": growth / 100,
                            "start_year": resolved_start,
                            "end_year": resolved_end,
                        }
                    )
                    _save_payload(conn, user_id, plan, updated, "income_edited")
                if remove:
                    updated = deepcopy(payload)
                    updated["income"].pop(index)
                    _save_payload(conn, user_id, plan, updated, "income_deleted")


def _render_spending_inputs(conn, user_id: int, plan: dict) -> None:
    payload = plan["payload"]
    st.subheader("Expenses")
    st.caption("Use one card for each recurring spending category.")
    suggestions = spending_suggestions(conn, user_id)
    if suggestions:
        with st.popover("Suggest from spending history", use_container_width=True):
            st.caption(
                f"Based on {suggestions[0]['months']} imported month(s). "
                "Median reduces the effect of occasional large purchases."
            )
            method = st.radio(
                "Suggestion method",
                ["Median", "Mean"],
                horizontal=True,
                key=f"spending_method_{plan['id']}",
            )
            suggestion_frame = pd.DataFrame(
                [
                    {
                        "Category": row["category"],
                        "Mean": row["mean_monthly"],
                        "Median": row["median_monthly"],
                    }
                    for row in suggestions
                ]
            )
            st.dataframe(suggestion_frame, use_container_width=True, hide_index=True)
            selected_categories = st.multiselect(
                "Categories to add",
                [row["category"] for row in suggestions],
                default=[row["category"] for row in suggestions],
                key=f"spending_suggestions_{plan['id']}",
            )
            replace_matches = st.checkbox(
                "Override matching plan expenses",
                value=False,
                help="When off, existing plan expenses keep their current amounts.",
            )
            if st.button(
                "Apply suggestions",
                type="primary",
                key=f"apply_spending_suggestions_{plan['id']}",
            ):
                updated = deepcopy(payload)
                existing = {
                    str(row.get("category") or "").casefold(): index
                    for index, row in enumerate(updated["spending"])
                }
                amount_key = "median_monthly" if method == "Median" else "mean_monthly"
                for suggestion in suggestions:
                    category = suggestion["category"]
                    if category not in selected_categories:
                        continue
                    proposed = {
                        "category": category,
                        "monthly_amount": suggestion[amount_key],
                        "inflation_rate": 0.025,
                        "is_essential": False,
                        "flexibility_type": "discretionary",
                        "is_override": True,
                        "suggestion_method": method.lower(),
                    }
                    match = existing.get(category.casefold())
                    if match is None:
                        updated["spending"].append(proposed)
                    elif replace_matches:
                        updated["spending"][match].update(proposed)
                _save_payload(conn, user_id, plan, updated, "spending_suggestions")

    with st.popover("＋ Add expense", use_container_width=True):
        with st.form(f"add_expense_{plan['id']}", clear_on_submit=True):
            category = st.text_input("Expense name")
            monthly = st.number_input("Monthly amount", min_value=0.0, step=50.0)
            flexibility = st.selectbox(
                "Flexibility",
                ["Essential", "Discretionary", "Hybrid", "Not spending"],
            )
            inflation = st.number_input("Annual inflation %", min_value=0.0, max_value=20.0, value=2.5)
            if st.form_submit_button("Add expense", type="primary"):
                if not category.strip():
                    st.error("Expense name is required.")
                else:
                    updated = deepcopy(payload)
                    updated["spending"].append(
                        {
                            "category": category.strip(),
                            "monthly_amount": monthly,
                            "inflation_rate": inflation / 100,
                            "is_essential": flexibility == "Essential",
                            "flexibility_type": flexibility.lower().replace(" ", "_"),
                            "is_override": True,
                        }
                    )
                    _save_payload(conn, user_id, plan, updated, "expense_added")

    if not payload["spending"]:
        st.info("No expenses yet.")
    for index, expense in enumerate(payload["spending"]):
        name = expense.get("category") or "Expense"
        with st.expander(f"{name} · {_money(float(expense.get('monthly_amount') or 0))}/month"):
            with st.form(f"edit_expense_{plan['id']}_{index}"):
                edited_name = st.text_input("Expense name", value=name)
                monthly = st.number_input(
                    "Monthly amount",
                    min_value=0.0,
                    value=float(expense.get("monthly_amount") or 0),
                    step=50.0,
                )
                flexibility_options = ["Essential", "Discretionary", "Hybrid", "Not spending"]
                saved_flexibility = str(
                    expense.get("flexibility_type")
                    or ("essential" if expense.get("is_essential") else "discretionary")
                ).replace("_", " ").title()
                flexibility = st.selectbox(
                    "Flexibility",
                    flexibility_options,
                    index=(
                        flexibility_options.index(saved_flexibility)
                        if saved_flexibility in flexibility_options
                        else 0
                    ),
                )
                save_col, delete_col = st.columns(2)
                save = save_col.form_submit_button("Save expense", type="primary")
                remove = delete_col.form_submit_button("Delete expense")
                if save:
                    updated = deepcopy(payload)
                    updated["spending"][index].update(
                        {
                            "category": edited_name.strip() or name,
                            "monthly_amount": monthly,
                            "is_essential": flexibility == "Essential",
                            "flexibility_type": flexibility.lower().replace(" ", "_"),
                            "is_override": True,
                        }
                    )
                    _save_payload(conn, user_id, plan, updated, "expense_edited")
                if remove:
                    updated = deepcopy(payload)
                    updated["spending"].pop(index)
                    _save_payload(conn, user_id, plan, updated, "expense_deleted")


def _render_account_inputs(conn, user_id: int, plan: dict) -> None:
    payload = plan["payload"]
    account_types = ["TFSA", "RRSP", "FHSA", "Taxable", "HISA", "RRIF"]
    st.subheader("Accounts")
    st.caption("Enter the balance available to this plan. Contribution-room tracking is not required.")
    with st.popover("＋ Add account", use_container_width=True):
        with st.form(f"add_account_{plan['id']}", clear_on_submit=True):
            account_type = st.selectbox("Account type", account_types)
            institution = st.text_input("Institution or nickname")
            balance = st.number_input("Current balance", min_value=0.0, step=1000.0)
            annual_return = st.number_input(
                "Expected annual return %",
                min_value=-20.0,
                max_value=30.0,
                value=5.0,
            )
            if st.form_submit_button("Add account", type="primary"):
                updated = deepcopy(payload)
                updated["accounts"].append(
                    {
                        "account_type": account_type,
                        "current_balance": balance,
                        "institution": institution.strip() or None,
                        "annual_return": annual_return / 100,
                    }
                )
                _save_payload(conn, user_id, plan, updated, "account_added")

    if not payload["accounts"]:
        st.info("No accounts yet.")
    for index, account in enumerate(payload["accounts"]):
        account_type = str(account.get("account_type") or "Account").upper()
        balance = float(account.get("current_balance") or 0)
        institution = account.get("institution") or "No institution"
        with st.expander(f"{account_type} · {_money(balance)} · {institution}"):
            with st.form(f"edit_account_{plan['id']}_{index}"):
                saved_type = account_type if account_type in account_types else "Taxable"
                edited_type = st.selectbox(
                    "Account type",
                    account_types,
                    index=account_types.index(saved_type),
                )
                edited_institution = st.text_input("Institution or nickname", value=institution)
                edited_balance = st.number_input(
                    "Current balance",
                    min_value=0.0,
                    value=balance,
                    step=1000.0,
                )
                annual_return = st.number_input(
                    "Expected annual return %",
                    min_value=-20.0,
                    max_value=30.0,
                    value=float(account.get("annual_return") or 0.05) * 100,
                )
                save_col, delete_col = st.columns(2)
                save = save_col.form_submit_button("Save account", type="primary")
                remove = delete_col.form_submit_button("Delete account")
                if save:
                    updated = deepcopy(payload)
                    updated["accounts"][index].update(
                        {
                            "account_type": edited_type,
                            "current_balance": edited_balance,
                            "institution": edited_institution.strip() or None,
                            "annual_return": annual_return / 100,
                        }
                    )
                    _save_payload(conn, user_id, plan, updated, "account_edited")
                if remove:
                    updated = deepcopy(payload)
                    updated["accounts"].pop(index)
                    _save_payload(conn, user_id, plan, updated, "account_deleted")


def _render_setup(conn, user_id: int, plan: dict) -> None:
    payload = plan["payload"]
    tabs = st.tabs(
        [
            "1. About You",
            "2. Income & Benefits",
            "3. Spending",
            "4. Accounts",
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
        _render_income_inputs(conn, user_id, plan)
        st.divider()
        st.subheader("Government benefits")
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
        _render_spending_inputs(conn, user_id, plan)

    with tabs[3]:
        _render_account_inputs(conn, user_id, plan)

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
    metric_options = {
        "Net Worth": "Net worth",
        "Total Income": "Total income",
        "Spending": "Spending",
        "Taxes": "Federal tax",
        "Annual Surplus": "Surplus",
    }
    control_left, control_middle, control_right = st.columns([2, 1, 1])
    selected_metric = control_left.selectbox(
        "Chart metric",
        list(metric_options),
        label_visibility="collapsed",
        key=f"plan_metric_{plan['id']}",
    )
    control_middle.caption(f"Target retirement · {target_year}")
    control_right.caption(f"{len(frame)} year view")
    metric_column = metric_options[selected_metric]
    invalid_income = [
        row
        for row in plan["payload"]["income"]
        if row.get("end_year") is not None
        and int(row["end_year"]) < int(plan["payload"]["assumptions"]["start_year"])
    ]
    if invalid_income:
        st.warning(
            "One or more income sources end before this plan begins, so they contribute $0. "
            "Open Edit plan inputs → Income & Benefits and correct the timing."
        )
    metrics = st.columns(3)
    metrics[0].metric("Starting net worth", _money(float(frame.iloc[0]["Net worth"])))
    metrics[1].metric("At target year", _money(float(target_row.iloc[0]["Net worth"])))
    metrics[2].metric("Ending net worth", _money(float(frame.iloc[-1]["Net worth"])))
    chart = go.Figure()
    chart.add_trace(
        go.Scatter(
            x=frame["Year"],
            y=frame[metric_column],
            mode="lines",
            name=selected_metric,
            line_color=PRIMARY,
            customdata=frame[["Age"]],
            hovertemplate=(
                "Year %{x}<br>Age %{customdata[0]}<br>"
                + selected_metric
                + " $%{y:,.0f}<extra></extra>"
            ),
        )
    )
    chart.add_vline(x=target_year, line_dash="dot", line_color=PRIMARY_LIGHT)
    style_figure(chart, height=430)
    chart.update_layout(
        yaxis_title=selected_metric,
        hovermode="x unified",
        showlegend=False,
    )
    st.plotly_chart(chart, use_container_width=True)
    st.caption(
        f"Deterministic {len(frame)}-year projection · "
        f"{float(plan['payload']['assumptions']['spending_inflation']):.1%} spending inflation"
    )


def _render_plan_sections(plan: dict) -> None:
    payload = plan["payload"]
    st.markdown("### Plan timeline")
    profile = payload["profile"]
    milestone_cols = st.columns(3)
    milestone_cols[0].metric("Plan starts", payload["assumptions"]["start_year"])
    milestone_cols[1].metric("Retirement", profile.get("target_retire_year") or "Not set")
    dob = profile.get("date_of_birth")
    if dob:
        life_year = date.fromisoformat(dob).year + 95
    else:
        life_year = "Not set"
    milestone_cols[2].metric("Planning horizon", life_year)

    st.markdown("### Plan inputs")
    left, right = st.columns(2)
    with left:
        with st.container(border=True):
            st.markdown("#### Accounts")
            total = sum(float(row.get("current_balance") or 0) for row in payload["accounts"])
            st.metric("Invested and saved", _money(total))
            if payload["accounts"]:
                st.caption(" · ".join(row.get("account_type", "Account") for row in payload["accounts"]))
            else:
                st.caption("No accounts configured")
        with st.container(border=True):
            st.markdown("#### Expenses")
            monthly = sum(float(row.get("monthly_amount") or 0) for row in payload["spending"])
            st.metric("Normal monthly spending", _money(monthly))
            st.caption(f"{len(payload['spending'])} spending categories")
    with right:
        with st.container(border=True):
            st.markdown("#### Income")
            annual = sum(float(row.get("annual_amount") or 0) for row in payload["income"])
            st.metric("Annual starting income", _money(annual))
            st.caption(f"{len(payload['income'])} income sources")
        with st.container(border=True):
            st.markdown("#### Benefits")
            benefit_names = [row.get("benefit_type", "Benefit") for row in payload["benefits"]]
            st.metric("Benefit elections", len(benefit_names))
            st.caption(" · ".join(benefit_names) if benefit_names else "No benefits configured")

    if st.button("Edit plan inputs", type="primary", key=f"edit_plan_{plan['id']}"):
        st.session_state.planning_edit_mode = True
        st.rerun()


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
            st.session_state.planning_workspace_plan_id = None
            st.rerun()

    st.divider()
    st.subheader("Danger zone")
    st.error("Permanently deleting a plan also deletes every saved revision. It cannot be undone.")
    with st.form(f"delete_plan_{plan['id']}"):
        confirmation = st.text_input(
            f"Type {plan['name']} to confirm deletion",
        )
        if st.form_submit_button(
            "Permanently delete plan",
            disabled=confirmation != plan["name"],
        ):
            delete_plan(conn, user_id, plan["id"])
            st.session_state.planning_workspace_plan_id = None
            st.session_state.planning_edit_mode = False
            st.rerun()


def render() -> None:
    user = st.session_state.get("user")
    if not user:
        st.info("Log in to build plans.")
        return
    user_id = int(user["id"])
    conn = get_connection()
    try:
        plans = list_plans(conn, user_id)
        requested_id = st.session_state.get("planning_workspace_plan_id")
        active = next((plan for plan in plans if plan["id"] == requested_id), None)

        if active is None:
            page_header(
                "Plans",
                "Your current position stays separate from the futures you want to explore.",
            )
            create_col, mode_col = st.columns([1, 2])
            with create_col:
                with st.popover("New plan", use_container_width=True):
                    with st.form("create_planning_plan"):
                        name = st.text_input("Plan name", value="My Plan")
                        source = st.radio(
                            "Starting point",
                            ["Current finances snapshot", "Blank plan"],
                        )
                        if st.form_submit_button("Create plan", type="primary"):
                            created = create_plan(
                                conn,
                                user_id,
                                name,
                                from_current_finances=source == "Current finances snapshot",
                            )
                            st.session_state.planning_workspace_plan_id = created["id"]
                            st.session_state.planning_edit_mode = source == "Blank plan"
                            st.rerun()
            with mode_col:
                st.caption("Create independent plans, duplicate alternatives, and compare outcomes.")
            if not plans:
                st.info("Create your first plan from current finances or begin with a blank plan.")
                return
            _render_plan_cards(conn, user_id, plans)
            return

        if st.session_state.get("planning_edit_mode", False):
            header_left, header_right = st.columns([4, 1])
            header_left.markdown(f"## Build {active['name']}")
            header_left.caption("Work through each section. The chart updates from saved revisions.")
            if header_right.button("Back to plan", use_container_width=True):
                st.session_state.planning_edit_mode = False
                st.rerun()
            preview, builder = st.columns([1.05, 1.4])
            with preview:
                st.markdown("### Live projection")
                _render_projection(active, _projection_frame(active))
            with builder:
                _render_setup(conn, user_id, active)
            return

        toolbar_back, toolbar_plan, toolbar_meta = st.columns([0.8, 2.2, 1])
        if toolbar_back.button("← All plans", use_container_width=True):
            st.session_state.planning_workspace_plan_id = None
            st.rerun()
        selected_name = toolbar_plan.selectbox(
            "Active plan",
            [plan["name"] for plan in plans],
            index=[plan["id"] for plan in plans].index(active["id"]),
            label_visibility="collapsed",
        )
        selected_plan = next(plan for plan in plans if plan["name"] == selected_name)
        if selected_plan["id"] != active["id"]:
            set_active_plan(conn, user_id, selected_plan["id"])
            st.session_state.planning_workspace_plan_id = selected_plan["id"]
            st.rerun()
        toolbar_meta.caption(f"Revision {active['revision_number']} · Deterministic")

        st.markdown(f"# {active['name']}")
        tabs = st.tabs(["Plan", "Cash Flow", "Tax Analytics", "Compare", "Plan Settings"])
        frame = _projection_frame(active)
        with tabs[0]:
            _render_projection(active, frame)
            st.divider()
            _render_plan_sections(active)
        with tabs[1]:
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
        with tabs[2]:
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
        with tabs[3]:
            _render_compare(plans, active)
        with tabs[4]:
            _render_settings(conn, user_id, active)
    finally:
        conn.close()
