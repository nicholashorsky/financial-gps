"""Spending dashboard and CSV import workspace."""

from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Iterable

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from budget.categorizer import CATEGORIES, add_user_rule, infer_transaction_type
from budget.csv_parser import parse_csv, preview_csv
from budget.importer import get_spending_summary, import_csv_transactions
from budget.narrator import csv_sync_message, spending_message
from shared.db import get_connection


def _guess_column(columns: Iterable[str], candidates: list[str]) -> str | None:
    lower_map = {str(col).strip().lower(): col for col in columns}
    for candidate in candidates:
        if candidate in lower_map:
            return lower_map[candidate]
    return None


def _month_key(value: str | date) -> str:
    text = value.isoformat() if isinstance(value, date) else str(value)
    return text[:7]


def _monthly_totals(conn, user_id: int) -> pd.DataFrame:
    rows = conn.execute(
        """
        SELECT substr(date, 1, 7) AS month,
               COALESCE(SUM(CASE WHEN amount > 0 AND is_excluded = 0 THEN amount ELSE 0 END), 0) AS income,
               COALESCE(SUM(CASE WHEN amount < 0 AND is_excluded = 0 THEN ABS(amount) ELSE 0 END), 0) AS spending
        FROM transactions
        WHERE user_id = ?
        GROUP BY substr(date, 1, 7)
        ORDER BY month ASC
        """,
        (user_id,),
    ).fetchall()
    return pd.DataFrame([dict(row) for row in rows])


def _current_month_range() -> tuple[str, str]:
    today = date.today()
    start = today.replace(day=1).isoformat()
    if today.month == 12:
        end = date(today.year + 1, 1, 1).isoformat()
    else:
        end = date(today.year, today.month + 1, 1).isoformat()
    return start, end


def _current_month_summary(conn, user_id: int) -> pd.DataFrame:
    start, end = _current_month_range()
    rows = conn.execute(
        """
        SELECT category, COALESCE(SUM(ABS(amount)), 0) AS total
        FROM transactions
        WHERE user_id = ? AND amount < 0 AND is_excluded = 0 AND date >= ? AND date < ?
        GROUP BY category
        ORDER BY total DESC, category ASC
        """,
        (user_id, start, end),
    ).fetchall()
    return pd.DataFrame([dict(row) for row in rows])


def _top_transactions(conn, user_id: int, limit: int = 10) -> pd.DataFrame:
    rows = conn.execute(
        """
        SELECT date, description, amount, category, transaction_type
        FROM transactions
        WHERE user_id = ? AND is_excluded = 0
        ORDER BY date DESC, ABS(amount) DESC
        LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()
    return pd.DataFrame([dict(row) for row in rows])


def _subscription_hunter(conn, user_id: int) -> list[tuple[str, int, float]]:
    rows = conn.execute(
        """
        SELECT description, COUNT(*) AS occurrences, ROUND(SUM(ABS(amount)), 2) AS total
        FROM transactions
        WHERE user_id = ? AND amount < 0 AND is_excluded = 0
        GROUP BY lower(description)
        HAVING occurrences >= 2
        ORDER BY total DESC, occurrences DESC
        LIMIT 5
        """,
        (user_id,),
    ).fetchall()
    return [(row["description"], int(row["occurrences"]), float(row["total"] or 0)) for row in rows]


def _accounts_frame(conn, user_id: int) -> pd.DataFrame:
    rows = conn.execute(
        """
        SELECT
            a.id,
            a.name,
            a.type,
            a.account_number_hint,
            a.last_imported_at,
            COUNT(t.id) AS transaction_count,
            COALESCE(SUM(CASE WHEN t.amount > 0 AND t.is_excluded = 0 THEN t.amount ELSE 0 END), 0) AS income,
            COALESCE(SUM(CASE WHEN t.amount < 0 AND t.is_excluded = 0 THEN ABS(t.amount) ELSE 0 END), 0) AS spending
        FROM accounts a
        LEFT JOIN transactions t ON t.account_id = a.id
        WHERE a.user_id = ?
        GROUP BY a.id
        ORDER BY a.type ASC, a.name ASC
        """,
        (user_id,),
    ).fetchall()
    return pd.DataFrame([dict(row) for row in rows])


def _review_transactions(conn, user_id: int, category_filter: str = "Needs review", limit: int = 50) -> list[dict]:
    where = "t.user_id = ? AND t.source = 'csv_import'"
    params: list[object] = [user_id]
    if category_filter == "Needs review":
        where += " AND COALESCE(t.category, 'Other') = 'Other'"
    elif category_filter != "All":
        where += " AND t.category = ?"
        params.append(category_filter)

    rows = conn.execute(
        f"""
        SELECT
            t.id,
            t.date,
            t.description,
            t.amount,
            COALESCE(t.category, 'Other') AS category,
            t.transaction_type,
            t.is_excluded,
            a.name AS account_name
        FROM transactions t
        LEFT JOIN accounts a ON a.id = t.account_id
        WHERE {where}
        ORDER BY t.date DESC, t.id DESC
        LIMIT ?
        """,
        (*params, limit),
    ).fetchall()
    return [dict(row) for row in rows]


def _keyword_hint(description: str) -> str:
    words = [part for part in description.lower().replace("*", " ").replace("#", " ").split() if len(part) > 2]
    return " ".join(words[:2]) if words else description.lower()[:24]


def _apply_category(conn, user_id: int, transaction_id: int, category: str) -> None:
    row = conn.execute(
        "SELECT description, amount FROM transactions WHERE id = ? AND user_id = ?",
        (transaction_id, user_id),
    ).fetchone()
    if not row:
        return
    transaction_type = infer_transaction_type(float(row["amount"] or 0), category, row["description"] or "")
    conn.execute(
        """
        UPDATE transactions
        SET category = ?, transaction_type = ?
        WHERE id = ? AND user_id = ?
        """,
        (category, transaction_type, transaction_id, user_id),
    )
    conn.commit()


def _create_rule_from_review(
    conn,
    user_id: int,
    keyword: str,
    category: str,
    *,
    apply_existing: bool,
) -> None:
    rule_id = add_user_rule(conn, user_id, keyword, category, priority=90)
    if not apply_existing:
        return
    like = f"%{keyword.strip().lower()}%"
    rows = conn.execute(
        """
        SELECT id, description, amount
        FROM transactions
        WHERE user_id = ?
          AND lower(description) LIKE ?
          AND COALESCE(category, 'Other') = 'Other'
        """,
        (user_id, like),
    ).fetchall()
    for row in rows:
        transaction_type = infer_transaction_type(float(row["amount"] or 0), category, row["description"] or "")
        conn.execute(
            "UPDATE transactions SET category = ?, transaction_type = ? WHERE id = ? AND user_id = ?",
            (category, transaction_type, row["id"], user_id),
        )
    conn.commit()
    st.session_state.last_rule_created = rule_id


def _render_metrics(summary) -> None:
    cols = st.columns(4)
    metrics = [
        ("Transactions", summary.transaction_count),
        ("Accounts", summary.account_count),
        ("Spending", f"${summary.spending_total:,.2f}"),
        ("Income", f"${summary.income_total:,.2f}"),
    ]
    for col, (label, value) in zip(cols, metrics, strict=False):
        col.metric(label, value)


def _render_category_chart(summary) -> None:
    if not summary.spending_by_category:
        st.info("No categorized spending yet. Import a CSV to wake the charts up.")
        return

    categories = [row["category"] or "Other" for row in summary.spending_by_category]
    totals = [float(row["total"] or 0) for row in summary.spending_by_category]
    figure = go.Figure(data=[go.Pie(labels=categories, values=totals, hole=0.45)])
    figure.update_layout(title="Current Month Spending Mix", height=340, margin=dict(l=20, r=20, t=40, b=20))
    st.plotly_chart(figure, use_container_width=True)


def _render_monthly_trend(conn, user_id: int) -> None:
    trend = _monthly_totals(conn, user_id)
    if trend.empty:
        st.info("Monthly trend will show up after the first import.")
        return

    figure = go.Figure()
    figure.add_trace(go.Bar(x=trend["month"], y=trend["spending"], name="Spending", marker_color="#dc2626"))
    figure.add_trace(go.Bar(x=trend["month"], y=trend["income"], name="Income", marker_color="#0f766e"))
    figure.update_layout(
        barmode="group",
        title="Monthly Trend",
        height=320,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    st.plotly_chart(figure, use_container_width=True)


def _render_recent_transactions(summary) -> None:
    if not summary.recent_transactions:
        st.info("Recent transactions will appear here after the first import.")
        return

    rows = []
    for row in summary.recent_transactions:
        rows.append(
            {
                "Date": row["date"],
                "Description": row["description"],
                "Amount": float(row["amount"] or 0),
                "Category": row["category"] or "Other",
                "Type": row["transaction_type"] or "expense",
                "Source": row["source"] or "csv_import",
            }
        )
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def _render_import_section(conn, user_id: int, summary) -> object:
    st.subheader("CSV Import")
    uploaded_file = st.file_uploader("Upload an RBC CSV export", type=["csv"], key="spending_csv_upload")
    if uploaded_file is None:
        st.caption("Use the sample CSV for beta testing, then switch to real exports when you trust the flow.")
        return summary

    file_bytes = uploaded_file.getvalue()
    parsed = parse_csv(file_bytes)
    preview = preview_csv(file_bytes)

    if parsed.warnings:
        for warning in parsed.warnings:
            st.warning(warning)

    st.write(f"Detected format: `{parsed.format_name}`")
    st.dataframe(preview, use_container_width=True, hide_index=True)

    column_map = None
    if parsed.needs_column_mapping:
        st.markdown("**Map the columns**")
        columns = list(preview.columns)
        date_col = st.selectbox(
            "Date column",
            options=columns,
            index=columns.index(_guess_column(columns, ["transaction date", "posting date", "date"]) or columns[0]),
        )
        description_col = st.selectbox(
            "Description column",
            options=columns,
            index=columns.index(_guess_column(columns, ["description", "description 1", "memo", "activity"]) or columns[0]),
        )
        amount_col = st.selectbox(
            "Amount column",
            options=columns,
            index=columns.index(_guess_column(columns, ["amount", "amount (cad)", "cad$", "debit", "credit"]) or columns[0]),
        )
        column_map = {"date": date_col, "description": description_col, "amount": amount_col}
        st.caption("The importer only needs date, description, and amount to begin with.")

    st.markdown("**Account names**")
    account_name_overrides: dict[str, str] = {}
    account_targets = parsed.accounts or []
    if not account_targets:
        st.info("No distinct accounts were detected. The import will use a single inferred account.")
    for account in account_targets:
        account_name_overrides[account.key] = st.text_input(
            f"{account.suggested_name} name",
            value=account.suggested_name,
            key=f"account_name_{account.key}",
        )

    if st.button("Import transactions", type="primary", use_container_width=True):
        result, categorized = import_csv_transactions(
            conn,
            user_id,
            file_bytes,
            column_map=column_map,
            account_name_overrides=account_name_overrides,
        )

        for warning in result.warnings:
            st.warning(warning)

        st.success(
            f"Imported {result.imported} transactions, skipped {result.skipped_duplicates} duplicates, and matched {result.transfers_matched} transfer pair(s)."
        )
        if result.bridge_fields_updated or result.bridge_fields_preserved:
            st.info(csv_sync_message(result.bridge_fields_updated, result.bridge_fields_preserved))
        if result.ghost_accounts:
            st.warning("New account(s) detected: " + ", ".join(result.ghost_accounts) + ".")

        if categorized:
            st.markdown("**Imported preview**")
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "Date": txn.date,
                            "Description": txn.description,
                            "Amount": txn.amount,
                            "Category": txn.category,
                            "Type": txn.transaction_type,
                        }
                        for txn in categorized[:10]
                    ]
                ),
                use_container_width=True,
                hide_index=True,
            )

        return get_spending_summary(conn, user_id)
    return summary


def _render_accounts_section(conn, user_id: int) -> None:
    st.subheader("Tracked Accounts")
    accounts = _accounts_frame(conn, user_id)
    if accounts.empty:
        st.info("No accounts are being tracked yet. Import a CSV to create account records.")
        return

    display = accounts.drop(columns=["id"]).rename(
        columns={
            "name": "Account",
            "type": "Type",
            "account_number_hint": "Hint",
            "last_imported_at": "Last import",
            "transaction_count": "Transactions",
            "income": "Income",
            "spending": "Spending",
        }
    )
    st.dataframe(display, use_container_width=True, hide_index=True)

    with st.expander("Rename an account"):
        account_options = {f"{row['name']} ({row['type']})": int(row["id"]) for _, row in accounts.iterrows()}
        selected = st.selectbox("Account", list(account_options.keys()))
        current_name = selected.rsplit(" (", 1)[0]
        new_name = st.text_input("Display name", value=current_name)
        if st.button("Save account name", use_container_width=True):
            conn.execute(
                "UPDATE accounts SET name = ? WHERE id = ? AND user_id = ?",
                (new_name.strip() or current_name, account_options[selected], user_id),
            )
            conn.commit()
            st.success("Account name updated.")
            st.rerun()


def _render_transaction_review(conn, user_id: int) -> None:
    st.subheader("Imported Transaction Review")
    st.caption("Review imported rows that landed in Other, then categorize them or turn a recurring description into a rule.")

    filter_options = ["Needs review", "All", *CATEGORIES]
    filter_choice = st.selectbox("Review filter", filter_options, index=0)
    transactions = _review_transactions(conn, user_id, filter_choice)
    if not transactions:
        st.success("No imported transactions need review for this filter.")
        return

    st.caption(f"Showing {len(transactions)} imported transaction(s).")
    for txn in transactions:
        title = f"{txn['date']} | {txn['description']} | ${float(txn['amount'] or 0):,.2f}"
        with st.expander(title):
            cols = st.columns([1, 1, 1])
            cols[0].write(f"Account: {txn.get('account_name') or 'Unassigned'}")
            cols[1].write(f"Current category: {txn['category']}")
            cols[2].write(f"Type: {txn.get('transaction_type') or 'expense'}")

            category_index = CATEGORIES.index(txn["category"]) if txn["category"] in CATEGORIES else CATEGORIES.index("Other")
            selected_category = st.selectbox(
                "Category",
                CATEGORIES,
                index=category_index,
                key=f"review_category_{txn['id']}",
            )
            rule_keyword = st.text_input(
                "Rule keyword",
                value=_keyword_hint(txn["description"]),
                key=f"review_keyword_{txn['id']}",
            )
            apply_existing = st.checkbox(
                "Apply this rule to existing uncategorized matches",
                value=True,
                key=f"review_apply_{txn['id']}",
            )

            action_cols = st.columns(2)
            if action_cols[0].button("Save category only", key=f"save_category_{txn['id']}", use_container_width=True):
                _apply_category(conn, user_id, int(txn["id"]), selected_category)
                st.success("Transaction updated.")
                st.rerun()
            if action_cols[1].button("Create rule and categorize", key=f"create_rule_{txn['id']}", use_container_width=True):
                if not rule_keyword.strip():
                    st.error("Rule keyword is required.")
                else:
                    _create_rule_from_review(
                        conn,
                        user_id,
                        rule_keyword,
                        selected_category,
                        apply_existing=apply_existing,
                    )
                    _apply_category(conn, user_id, int(txn["id"]), selected_category)
                    st.success("Rule created and transaction updated.")
                    st.rerun()


def render() -> None:
    st.title("Spending")
    st.caption("Track accounts, import CSVs, and clean up the transaction categories that rules could not infer.")

    user = st.session_state.get("user")
    if not user:
        st.info("Log in to import transactions and review spending.")
        return

    user_id = int(user["id"])
    conn = get_connection()
    try:
        summary = get_spending_summary(conn, user_id)
        _render_metrics(summary)

        top_category = summary.spending_by_category[0]["category"] if summary.spending_by_category else None
        st.info(spending_message(summary.spending_total, top_category))

        tab_import, tab_accounts, tab_review, tab_insights = st.tabs(
            ["Import", "Accounts", "Transaction Review", "Insights"]
        )
        with tab_import:
            summary = _render_import_section(conn, user_id, summary)
        with tab_accounts:
            _render_accounts_section(conn, user_id)
        with tab_review:
            _render_transaction_review(conn, user_id)
        with tab_insights:
            left, right = st.columns([1.1, 0.9])
            with left:
                st.subheader("Spending by Category")
                _render_category_chart(summary)
                st.subheader("Monthly Trend")
                _render_monthly_trend(conn, user_id)
            with right:
                st.subheader("Recent Transactions")
                _render_recent_transactions(summary)
                st.subheader("Subscription Hunter")
                subscriptions = _subscription_hunter(conn, user_id)
                if not subscriptions:
                    st.info("No obvious recurring charges yet.")
                else:
                    for description, occurrences, total in subscriptions:
                        st.write(f"{description} - {occurrences} hits, ${total:,.2f}")
    finally:
        conn.close()
