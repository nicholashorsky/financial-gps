"""FIRE Financial Profile - income, spending, account balances."""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from shared.db import get_connection
from shared.fire_service import (
    get_or_create_fire_profile,
    list_fire_income_sources,
    list_fire_spending_baseline,
    list_investment_accounts,
    save_fire_profile,
    upsert_fire_income_source,
    upsert_fire_spending_category,
    upsert_investment_account,
)


ACCOUNT_TYPES = ["TFSA", "RRSP", "FHSA", "taxable", "HISA"]


def _source_badge(is_override: object) -> str:
    return "✏️ Edited" if int(is_override or 0) == 1 else "📊 From your transactions"


def render() -> None:
    st.title("FIRE Planner - Financial Profile")
    st.caption("Tell the forecast about you, your normal spending, and the accounts funding your plan.")

    user = st.session_state.get("user")
    if not user:
        st.info("Log in to build a FIRE profile.")
        return

    user_id = int(user["id"])
    conn = get_connection()
    try:
        profile = get_or_create_fire_profile(conn, user_id)
        income_sources = list_fire_income_sources(conn, user_id)
        spending_rows = list_fire_spending_baseline(conn, user_id)
        accounts = list_investment_accounts(conn, user_id)

        with st.form("fire_profile_form"):
            st.subheader("1. About you")
            st.caption("These details control tax assumptions and the timing of CPP, OAS, and registered-account rules.")
            left, right = st.columns(2)
            with left:
                province = st.selectbox(
                    "Province of residence",
                    ["", "ON", "BC", "AB", "QC"],
                    index=["", "ON", "BC", "AB", "QC"].index(profile.get("province") or ""),
                    help="Used to select provincial tax assumptions. Choose where you currently live.",
                )
                dob_value = date.fromisoformat(profile["date_of_birth"]) if profile.get("date_of_birth") else date(1990, 1, 1)
                dob = st.date_input(
                    "Complete date of birth",
                    value=dob_value,
                    min_value=date(1900, 1, 1),
                    max_value=date.today(),
                    format="YYYY-MM-DD",
                    help="Enter the year, month, and day. The forecast uses your exact age for benefit and RRIF timing.",
                )
            with right:
                resident = st.checkbox(
                    "I currently live in Canada",
                    value=bool(profile.get("is_canadian_resident", 1)),
                    help="Current residency can affect registered-account room and benefit assumptions.",
                )
                saved_years = profile.get("years_in_canada_post_18")
                years_in_canada = st.number_input(
                    "Years lived in Canada since age 18",
                    min_value=0,
                    max_value=60,
                    value=int(saved_years if saved_years is not None else 40),
                    help="OAS is generally based on years of Canadian residence after age 18. Enter your best current estimate, up to 40 for a full-pension estimate.",
                )
                st.caption("This is separate from citizenship. It helps estimate OAS eligibility and the pension amount.")

            st.subheader("2. Income used by the forecast")
            st.caption("Enter income before income tax, CPP, EI, benefit deductions, or other payroll deductions.")
            income_left, income_right = st.columns([1, 1])
            with income_left:
                employment_row = next((row for row in income_sources if row["source_type"] == "employment"), None)
                employment_amount = float(employment_row["annual_amount"] or 0) if employment_row else 0.0
                employment_income = st.number_input(
                    "Annual gross employment income",
                    min_value=0.0,
                    value=employment_amount,
                    step=1000.0,
                    help="Use your expected annual salary or other employment income before deductions.",
                )
                if employment_row:
                    st.caption(_source_badge(employment_row.get("is_override")))
                    if not bool(employment_row.get("is_override")):
                        st.warning(
                            "This starting value was estimated from bank deposits, which are usually after tax. "
                            "Replace it with gross annual income for a more useful forecast."
                        )
            with income_right:
                st.info(
                    "Taxes are not imported from your bank deposits. The FIRE forecast estimates federal and "
                    "provincial income tax from this gross amount, then adds any taxable retirement withdrawals."
                )
                st.caption("You can review CPP and OAS estimates separately in Benefits Workspace.")

            st.subheader("3. Normal monthly spending")
            st.caption("Transaction-derived amounts are a starting point. Edit any category that is not representative of a normal month.")
            spending_inputs: list[tuple[str, float, bool]] = []
            if not spending_rows:
                st.info("No spending baseline yet. Import transactions or start entering categories here.")
                spending_rows = [
                    {"category": "Housing", "monthly_amount": 0.0, "is_override": 1},
                    {"category": "Groceries", "monthly_amount": 0.0, "is_override": 1},
                    {"category": "Transportation", "monthly_amount": 0.0, "is_override": 1},
                ]
            spend_cols = st.columns(3)
            for idx, row in enumerate(spending_rows):
                col = spend_cols[idx % 3]
                with col:
                    amount = st.number_input(
                        row["category"],
                        min_value=0.0,
                        value=float(row["monthly_amount"] or 0),
                        step=50.0,
                        key=f"fire_spend_{row['category']}",
                    )
                    st.caption(_source_badge(row.get("is_override")))
                    spending_inputs.append((row["category"], amount, True))

            st.subheader("4. Investment and savings balances")
            st.caption("Enter current balances. These are planning values and do not alter imported bank transactions.")
            account_inputs: list[tuple[str, float]] = []
            account_map = {row["account_type"]: row for row in accounts}
            acct_cols = st.columns(len(ACCOUNT_TYPES))
            for acct_type, col in zip(ACCOUNT_TYPES, acct_cols, strict=False):
                current = float(account_map.get(acct_type, {}).get("current_balance") or 0)
                with col:
                    balance = st.number_input(acct_type, min_value=0.0, value=current, step=500.0, key=f"acct_{acct_type}")
                    account_inputs.append((acct_type, balance))

            submitted = st.form_submit_button("Save profile", type="primary")
            if submitted:
                save_fire_profile(
                    conn,
                    user_id,
                    province=province or None,
                    date_of_birth=dob,
                    years_in_canada_post_18=years_in_canada,
                    is_canadian_resident=resident,
                    is_quebec=(province == "QC"),
                )
                upsert_fire_income_source(conn, user_id, "employment", employment_income, is_override=True)
                for category, amount, is_essential in spending_inputs:
                    upsert_fire_spending_category(conn, user_id, category, amount, is_essential=is_essential, is_override=True)
                for acct_type, balance in account_inputs:
                    upsert_investment_account(conn, user_id, acct_type, balance)
                st.success("FIRE profile saved.")
                st.rerun()

        st.divider()
        st.subheader("Current profile snapshot")
        st.dataframe(
            pd.DataFrame(
                [
                    {"Type": "Income source", "Count": len(income_sources)},
                    {"Type": "Spending categories", "Count": len(spending_rows)},
                    {"Type": "Investment accounts", "Count": len(accounts)},
                ]
            ),
            use_container_width=True,
            hide_index=True,
        )
    finally:
        conn.close()
