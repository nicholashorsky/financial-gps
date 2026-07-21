"""Spending dashboard and CSV import workspace."""

from __future__ import annotations

from datetime import date, timedelta
import re
from typing import Iterable

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from budget.categorizer import add_user_rule, get_user_categories, infer_transaction_type, normalize_text
from budget.csv_parser import parse_csv, preview_csv
from budget.importer import get_spending_summary, import_csv_transactions, list_import_batches, undo_import_batch
from budget.narrator import csv_sync_message, spending_message
from shared.db import get_connection
from shared.formatting import format_currency as _format_money, format_date, format_month
from shared.theme import INCOME, SPENDING, style_figure
from shared.ui import page_header


UNREVIEWED_SQL = "COALESCE(category, 'Uncategorized') IN ('', 'Uncategorized')"
UNREVIEWED_TXN_SQL = "COALESCE(t.category, 'Uncategorized') IN ('', 'Uncategorized')"


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
               COALESCE(SUM(CASE WHEN amount > 0 AND is_excluded = 0 AND COALESCE(category, '') <> 'Transfer' THEN amount ELSE 0 END), 0) AS income,
               COALESCE(SUM(CASE WHEN amount < 0 AND is_excluded = 0 AND COALESCE(category, '') <> 'Transfer' THEN ABS(amount) ELSE 0 END), 0) AS spending
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


def _overview_period_range(period: str, today: date | None = None) -> tuple[str | None, str | None, str | None, str | None]:
    today = today or date.today()
    end = today + timedelta(days=1)
    if period == "This month":
        start = today.replace(day=1)
        days = (end - start).days
    elif period == "All time":
        return None, None, None, None
    else:
        start = today - timedelta(days=29)
        days = 30
    return start.isoformat(), end.isoformat(), (start - timedelta(days=days)).isoformat(), start.isoformat()


def _period_overview(conn, user_id: int, period: str, today: date | None = None) -> dict[str, object]:
    start, end, previous_start, previous_end = _overview_period_range(period, today)
    date_filter = "" if start is None else "AND date >= ? AND date < ?"
    params: list[object] = [user_id]
    if start is not None:
        params.extend([start, end])
    row = conn.execute(
        f"""
        SELECT
            COALESCE(SUM(CASE WHEN amount < 0 AND is_excluded = 0 AND COALESCE(category, '') <> 'Transfer' THEN ABS(amount) ELSE 0 END), 0) AS spending,
            COALESCE(SUM(CASE WHEN amount > 0 AND is_excluded = 0 AND COALESCE(category, '') <> 'Transfer' THEN amount ELSE 0 END), 0) AS income
        FROM transactions WHERE user_id = ? {date_filter}
        """,
        params,
    ).fetchone()
    previous_spending: float | None = None
    if previous_start is not None:
        previous_spending = float(
            conn.execute(
                """
                SELECT COALESCE(SUM(ABS(amount)), 0) FROM transactions
                WHERE user_id = ? AND amount < 0 AND is_excluded = 0
                  AND COALESCE(category, '') <> 'Transfer' AND date >= ? AND date < ?
                """,
                (user_id, previous_start, previous_end),
            ).fetchone()[0]
        )
    categories = conn.execute(
        f"""
        SELECT COALESCE(category, 'Other') AS category, SUM(ABS(amount)) AS total
        FROM transactions
        WHERE user_id = ? AND amount < 0 AND is_excluded = 0
          AND COALESCE(category, '') <> 'Transfer' {date_filter}
        GROUP BY category ORDER BY total DESC, category ASC LIMIT 5
        """,
        params,
    ).fetchall()
    spending = float(row["spending"] or 0)
    income = float(row["income"] or 0)
    return {
        "spending": spending,
        "income": income,
        "net": income - spending,
        "previous_spending": previous_spending,
        "categories": [dict(category) for category in categories],
    }


def _current_month_summary(conn, user_id: int) -> pd.DataFrame:
    start, end = _current_month_range()
    rows = conn.execute(
        """
        SELECT category, COALESCE(SUM(ABS(amount)), 0) AS total
        FROM transactions
        WHERE user_id = ? AND amount < 0 AND is_excluded = 0
          AND COALESCE(category, '') <> 'Transfer' AND date >= ? AND date < ?
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
        WHERE user_id = ? AND amount < 0 AND is_excluded = 0 AND COALESCE(category, '') <> 'Transfer'
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
            a.balance,
            a.account_number_hint,
            a.last_imported_at,
            MAX(t.date) AS last_transaction_date,
            COUNT(t.id) AS transaction_count,
            COALESCE(SUM(CASE WHEN t.amount > 0 AND t.is_excluded = 0 THEN t.amount ELSE 0 END), 0) AS income,
            COALESCE(SUM(CASE WHEN t.amount < 0 AND t.is_excluded = 0 THEN ABS(t.amount) ELSE 0 END), 0) AS spending,
            COALESCE(SUM(CASE WHEN t.is_excluded = 0 THEN t.amount ELSE 0 END), 0) AS net_flow
        FROM accounts a
        LEFT JOIN transactions t ON t.account_id = a.id
        WHERE a.user_id = ?
        GROUP BY a.id
        ORDER BY a.type ASC, a.name ASC
        """,
        (user_id,),
    ).fetchall()
    return pd.DataFrame([dict(row) for row in rows])


def _spending_workbench_stats(conn, user_id: int) -> dict[str, float | int]:
    start, end = _current_month_range()
    row = conn.execute(
        f"""
        SELECT
            COALESCE(SUM(CASE WHEN amount > 0 AND is_excluded = 0 AND COALESCE(category, '') <> 'Transfer' AND date >= ? AND date < ? THEN amount ELSE 0 END), 0) AS month_income,
            COALESCE(SUM(CASE WHEN amount < 0 AND is_excluded = 0 AND COALESCE(category, '') <> 'Transfer' AND date >= ? AND date < ? THEN ABS(amount) ELSE 0 END), 0) AS month_spending,
            COALESCE(SUM(CASE WHEN is_excluded = 0 AND COALESCE(category, '') <> 'Transfer' AND date >= ? AND date < ? THEN amount ELSE 0 END), 0) AS month_net,
            SUM(CASE WHEN source = 'csv_import' AND {UNREVIEWED_SQL} THEN 1 ELSE 0 END) AS review_count,
            SUM(CASE WHEN is_excluded = 1 THEN 1 ELSE 0 END) AS excluded_count
        FROM transactions
        WHERE user_id = ?
        """,
        (start, end, start, end, start, end, user_id),
    ).fetchone()
    return {
        "month_income": float(row["month_income"] or 0),
        "month_spending": float(row["month_spending"] or 0),
        "month_net": float(row["month_net"] or 0),
        "review_count": int(row["review_count"] or 0),
        "excluded_count": int(row["excluded_count"] or 0),
    }


def _review_transactions(
    conn,
    user_id: int,
    category_filter: str = "Needs review",
    account_id: int | None = None,
    search: str = "",
) -> list[dict]:
    where = "t.user_id = ? AND t.source = 'csv_import'"
    params: list[object] = [user_id]
    if category_filter == "Needs review":
        where += f" AND {UNREVIEWED_TXN_SQL}"
    elif category_filter != "All":
        where += " AND t.category = ?"
        params.append(category_filter)
    if account_id is not None:
        where += " AND t.account_id = ?"
        params.append(account_id)
    if search.strip():
        where += " AND lower(t.description) LIKE ?"
        params.append(f"%{search.strip().lower()}%")

    rows = conn.execute(
        f"""
        SELECT
            t.id,
            t.date,
            t.description,
            t.amount,
            COALESCE(t.category, 'Uncategorized') AS category,
            t.transaction_type,
            t.is_excluded,
            a.name AS account_name
        FROM transactions t
        LEFT JOIN accounts a ON a.id = t.account_id
        WHERE {where}
        ORDER BY t.date ASC, t.id ASC
        """,
        params,
    ).fetchall()
    return [dict(row) for row in rows]


def _navigate_spending(section: str) -> None:
    st.session_state.spending_section = section


def _keyword_hint(description: str) -> str:
    words = [part for part in description.lower().replace("*", " ").replace("#", " ").split() if len(part) > 2]
    return " ".join(words[:2]) if words else description.lower()[:24]


def _rule_keyword_from_description(description: str) -> str:
    normalized = re.sub(r"[^a-z0-9 ]+", " ", description.lower())
    normalized = re.sub(r"\b\d+\b", " ", normalized)
    tokens = [
        token
        for token in normalized.split()
        if len(token) > 2
        and token
        not in {
            "the",
            "and",
            "inc",
            "ltd",
            "canada",
            "guelph",
            "toronto",
            "online",
            "rao",
        }
    ]
    if not tokens:
        return _keyword_hint(description)
    if tokens[0] == "transfer" and len(tokens) > 1:
        tokens = tokens[1:]
    if tokens[0] in {"amzn", "amazon", "amazonca"}:
        return "amazon"
    if len(tokens) >= 2 and tokens[0] == "wal" and tokens[1] == "mart":
        return "wal mart"
    if tokens[0] == "walmart":
        return "walmart"
    return " ".join(tokens[:2])


def _review_session_progress(
    session_ids: set[int],
    current_ids: set[int],
    skipped_ids: set[int],
) -> dict[str, int]:
    """Return stable progress counts for the current review session."""

    tracked_ids = session_ids | current_ids
    skipped = len(tracked_ids & current_ids & skipped_ids)
    completed = len(tracked_ids - current_ids)
    remaining = len(current_ids - skipped_ids)
    return {
        "total": len(tracked_ids),
        "completed": completed,
        "remaining": remaining,
        "skipped": skipped,
    }


def _rule_preview(conn, user_id: int, keyword: str) -> dict[str, object]:
    """Describe the user-scoped rows a review rule would update."""

    normalized_keyword = normalize_text(keyword)
    if not normalized_keyword:
        return {"count": 0, "accounts": []}

    rows = conn.execute(
        f"""
        SELECT DISTINCT t.id, t.description, COALESCE(a.name, 'Unassigned account') AS account_name
        FROM transactions t
        LEFT JOIN accounts a ON a.id = t.account_id AND a.user_id = t.user_id
        WHERE t.user_id = ?
          AND {UNREVIEWED_TXN_SQL}
        ORDER BY account_name ASC
        """,
        (user_id,),
    ).fetchall()
    matching_rows = [row for row in rows if normalized_keyword in normalize_text(row["description"] or "")]
    return {
        "count": len(matching_rows),
        "accounts": sorted({str(row["account_name"]) for row in matching_rows}),
    }


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
    normalized_keyword = normalize_text(keyword)
    rows = conn.execute(
        f"""
        SELECT id, description, amount
        FROM transactions
        WHERE user_id = ?
          AND {UNREVIEWED_SQL}
        """,
        (user_id,),
    ).fetchall()
    for row in rows:
        if normalized_keyword not in normalize_text(row["description"] or ""):
            continue
        transaction_type = infer_transaction_type(float(row["amount"] or 0), category, row["description"] or "")
        conn.execute(
            "UPDATE transactions SET category = ?, transaction_type = ? WHERE id = ? AND user_id = ?",
            (category, transaction_type, row["id"], user_id),
        )
    conn.commit()
    st.session_state.last_rule_created = rule_id


def _skip_review_transaction(transaction_id: int) -> None:
    skipped = set(st.session_state.get("spending_review_skipped", set()))
    skipped.add(transaction_id)
    st.session_state.spending_review_skipped = skipped


def _clear_review_skips() -> None:
    st.session_state.spending_review_skipped = set()


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
    style_figure(figure, height=340)
    st.plotly_chart(figure, use_container_width=True)


def _render_monthly_trend(conn, user_id: int) -> None:
    trend = _monthly_totals(conn, user_id)
    if trend.empty:
        st.info("Monthly trend will show up after the first import.")
        return

    figure = go.Figure()
    month_labels = [format_month(month) for month in trend["month"]]
    figure.add_trace(go.Bar(x=month_labels, y=trend["spending"], name="Spending", marker_color=SPENDING))
    figure.add_trace(go.Bar(x=month_labels, y=trend["income"], name="Income", marker_color=INCOME))
    figure.update_layout(
        barmode="group",
        title="Monthly Trend",
        height=320,
        margin=dict(l=20, r=20, t=40, b=20),
    )
    style_figure(figure)
    figure.update_xaxes(type="category")
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


def _render_workbench_header(conn, user_id: int, summary) -> None:
    stats = _spending_workbench_stats(conn, user_id)
    review_count = int(stats["review_count"])
    if review_count > 0:
        st.warning(f"Review uncategorized transactions: {review_count} remaining")
    else:
        top_category = summary.spending_by_category[0]["category"] if summary.spending_by_category else None
        st.info(spending_message(summary.spending_total, top_category))

    cols = st.columns(4)
    cols[0].metric("This month in", _format_money(float(stats["month_income"])))
    cols[1].metric("This month out", _format_money(float(stats["month_spending"])))
    cols[2].metric("Net flow", _format_money(float(stats["month_net"])))
    cols[3].metric("Tracked accounts", summary.account_count)


def _render_review_banner(stats: dict[str, float | int]) -> None:
    review_count = int(stats["review_count"])
    if review_count > 0:
        with st.container(border=True):
            message_col, action_col = st.columns([4, 1.2])
            message_col.subheader(f"{review_count} transactions need your attention")
            message_col.caption("Review uncertain categories before relying on your spending totals.")
            action_col.button(
                "Review transactions",
                type="primary",
                use_container_width=True,
                on_click=_navigate_spending,
                args=("Transactions",),
            )
        return
    st.success("Transaction review is clear. The numbers are allowed to be smug for a moment.")


def _render_recent_transaction_list(conn, user_id: int, limit: int = 8) -> None:
    rows = conn.execute(
        """
        SELECT t.date, t.description, t.amount, COALESCE(t.category, 'Other') AS category, a.name AS account_name
        FROM transactions t
        LEFT JOIN accounts a ON a.id = t.account_id
        WHERE t.user_id = ?
        ORDER BY t.date DESC, t.id DESC
        LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()
    if not rows:
        st.info("Recent transactions will appear after the first import.")
        return

    for row in rows:
        amount = float(row["amount"] or 0)
        cols = st.columns([0.55, 2.1, 1.2, 1, 0.9])
        cols[0].caption(format_date(row["date"]))
        cols[1].write(row["description"] or "Transaction")
        cols[2].caption(row["account_name"] or "Unassigned")
        cols[3].caption(row["category"])
        cols[4].write(_format_money(amount))


def _render_top_accounts(accounts: pd.DataFrame, limit: int = 4) -> None:
    if accounts.empty:
        st.info("Accounts will appear here after the first import.")
        return
    top_accounts = accounts.sort_values("transaction_count", ascending=False).head(limit)
    for _, row in top_accounts.iterrows():
        with st.container(border=True):
            cols = st.columns([0.45, 2, 1])
            cols[0].markdown(f"### {str(row['name'])[:3].upper()}")
            cols[1].write(row["name"])
            updated = format_date(row["last_transaction_date"], fallback="Never")
            cols[1].caption(f"{str(row['type']).title()} · Updated {updated} · {int(row['transaction_count'])} transactions")
            cols[1].caption("Included in totals")
            balance = float(row["balance"] or 0)
            cols[2].write(_format_money(balance))
            cols[2].caption(f"{_format_money(float(row['net_flow'] or 0))} net flow")


def _render_category_snapshot(period_data: dict[str, object]) -> None:
    categories = period_data["categories"]
    if not categories:
        st.info("Category totals will appear after imports are categorized.")
        return
    spending = float(period_data["spending"] or 0)
    for row in categories:
        total = float(row["total"] or 0)
        cols = st.columns([3, 1])
        cols[0].write(row["category"] or "Other")
        cols[1].write(_format_money(total))
        st.progress(total / spending if spending else 0)


def _render_overview_section(conn, user_id: int, summary) -> None:
    stats = _spending_workbench_stats(conn, user_id)
    accounts = _accounts_frame(conn, user_id)

    _render_review_banner(stats)

    st.divider()
    left, right = st.columns([1, 1])
    with left:
        heading, action = st.columns([3, 1])
        heading.subheader("Accounts")
        action.button("Manage", use_container_width=True, on_click=_navigate_spending, args=("Accounts",))
        _render_top_accounts(accounts)
    with right:
        heading, selector = st.columns([2, 1.2])
        heading.subheader("Spending overview")
        period = selector.selectbox("Period", ["Last 30 days", "This month", "All time"], label_visibility="collapsed")
        period_data = _period_overview(conn, user_id, period)
        previous = period_data["previous_spending"]
        delta = None
        if previous:
            delta = f"{((float(period_data['spending']) - float(previous)) / float(previous)) * 100:+.1f}% vs previous period"
        st.metric("Total spent", _format_money(float(period_data["spending"])), delta=delta, delta_color="inverse")
        metrics = st.columns(2)
        metrics[0].metric("Income", _format_money(float(period_data["income"])))
        metrics[1].metric("Net flow", _format_money(float(period_data["net"])))
        _render_category_snapshot(period_data)

    st.divider()
    heading, action = st.columns([3, 1])
    heading.subheader("Recent transactions")
    action.button("View all", use_container_width=True, on_click=_navigate_spending, args=("Transactions",))
    _render_recent_transaction_list(conn, user_id)


def _render_import_section(conn, user_id: int, summary) -> object:
    st.subheader("CSV Import")
    _render_import_history(conn, user_id)
    uploaded_file = st.file_uploader("Upload an RBC CSV export", type=["csv"], key="spending_csv_upload")
    if uploaded_file is None:
        st.caption("Use the sample CSV for beta testing, then switch to real exports when you trust the flow.")
        return summary

    file_bytes = uploaded_file.getvalue()
    try:
        parsed = parse_csv(file_bytes)
        preview = preview_csv(file_bytes)
    except Exception as exc:
        st.error(f"This CSV could not be read: {exc}")
        return summary

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

    with st.container(border=True):
        st.markdown("**Confirm import**")
        st.write(f"File: `{uploaded_file.name}`")
        st.write(f"Parsed transactions: **{len(parsed.transactions)}** · Detected accounts: **{len(account_targets)}**")
        if parsed.skipped_invalid:
            st.warning(f"{parsed.skipped_invalid} invalid row(s) will be skipped.")
        st.caption("Duplicates will be skipped. You can undo newly imported rows from Import history.")

    import_disabled = not parsed.transactions and column_map is None
    if st.button("Confirm and import", type="primary", use_container_width=True, disabled=import_disabled):
        result, categorized = import_csv_transactions(
            conn,
            user_id,
            file_bytes,
            column_map=column_map,
            account_name_overrides=account_name_overrides,
            filename=uploaded_file.name,
        )

        for warning in result.warnings:
            st.warning(warning)

        st.success(
            f"Imported {result.imported} transactions, skipped {result.skipped_duplicates} duplicates, "
            f"rejected {result.skipped_invalid} invalid row(s), and matched {result.transfers_matched} transfer pair(s)."
        )
        if result.skipped_invalid:
            st.warning(
                f"{result.skipped_invalid} row(s) were not imported because the date, description, or amount was invalid."
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


def _render_import_history(conn, user_id: int) -> None:
    batches = list_import_batches(conn, user_id)
    with st.expander("Import history", expanded=False):
        if not batches:
            st.caption("Completed imports will appear here.")
            return
        for batch in batches:
            with st.container(border=True):
                cols = st.columns([2.2, 1, 1, 1])
                cols[0].write(batch["filename"])
                cols[0].caption(f"{batch['created_at']} · {batch['format_name']}")
                cols[1].metric("Imported", int(batch["imported_count"] or 0))
                cols[2].metric("Duplicates", int(batch["duplicate_count"] or 0))
                cols[3].metric("Transfers", int(batch["transfer_count"] or 0))
                if batch["undone_at"]:
                    st.caption(f"Undone {batch['undone_at']}")
                    continue
                batch_id = int(batch["id"])
                confirm_key = f"confirm_undo_import_{batch_id}"
                if not st.session_state.get(confirm_key):
                    if st.button("Undo this import", key=f"undo_import_{batch_id}"):
                        st.session_state[confirm_key] = True
                        st.rerun()
                else:
                    st.warning("This removes only transactions newly added by this import. Accounts and duplicate rows are preserved.")
                    actions = st.columns(2)
                    if actions[0].button("Cancel", key=f"cancel_undo_{batch_id}", use_container_width=True):
                        st.session_state[confirm_key] = False
                        st.rerun()
                    if actions[1].button("Confirm undo", key=f"confirm_undo_{batch_id}", type="primary", use_container_width=True):
                        deleted = undo_import_batch(conn, user_id, batch_id)
                        st.session_state[confirm_key] = False
                        st.success(f"Removed {deleted} transaction(s) from this import.")
                        st.rerun()


def _render_accounts_section(conn, user_id: int) -> None:
    st.subheader("Tracked Accounts")
    accounts = _accounts_frame(conn, user_id)
    if accounts.empty:
        st.info("No accounts are being tracked yet. Import a CSV to create account records.")
        return

    type_labels = {
        "chequing": "Cash",
        "savings": "Savings",
        "credit": "Credit Cards",
        "investment": "Investments",
    }
    groups = accounts.groupby("type", sort=True)
    group_cols = st.columns(min(len(groups), 4) or 1)
    for col, (account_type, group) in zip(group_cols, groups, strict=False):
        with col:
            label = type_labels.get(str(account_type), str(account_type).title())
            st.markdown(f"**{label}**")
            st.metric("Net flow", _format_money(float(group["net_flow"].sum())))
            st.caption(f"{int(group['transaction_count'].sum())} transaction(s)")

    st.divider()
    display = accounts.drop(columns=["id"]).rename(
        columns={
            "name": "Account",
            "type": "Type",
            "account_number_hint": "Hint",
            "last_imported_at": "Last import",
            "last_transaction_date": "Last transaction",
            "transaction_count": "Transactions",
            "income": "Income",
            "spending": "Spending",
            "net_flow": "Net flow",
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
    st.subheader("Transaction Review")
    st.caption("A cleanup queue for imported rows, inspired by the kind of review flow personal finance apps make you wish banks had built first.")

    categories = get_user_categories(conn, user_id)
    filter_options = ["Needs review", "All", *categories]
    accounts = _accounts_frame(conn, user_id)
    account_options = {"All accounts": None}
    if not accounts.empty:
        account_options.update({str(row["name"]): int(row["id"]) for _, row in accounts.iterrows()})

    filter_col, account_col, search_col = st.columns([1, 1, 1.4])
    filter_choice = filter_col.selectbox("Review filter", filter_options, index=0)
    account_choice = account_col.selectbox("Account", list(account_options.keys()))
    search = search_col.text_input("Search descriptions")

    transactions = _review_transactions(
        conn,
        user_id,
        filter_choice,
        account_id=account_options[account_choice],
        search=search,
    )
    if not transactions:
        st.success("No imported transactions need review for this filter.")
        return

    review_mode = st.segmented_control(
        "Review mode",
        ["Quick review", "Detailed list"],
        default="Quick review",
        key="transaction_review_mode",
    )
    if review_mode == "Quick review":
        session_key = f"{filter_choice}|{account_options[account_choice]}|{search.strip().lower()}"
        _render_quick_review(conn, user_id, transactions, categories, session_key=session_key)
        return

    st.caption(f"Showing {len(transactions)} imported transaction(s).")
    for txn in transactions:
        title = f"{txn['date']} | {txn['description']} | ${float(txn['amount'] or 0):,.2f}"
        with st.expander(title):
            cols = st.columns([1, 1, 1])
            cols[0].write(f"Account: {txn.get('account_name') or 'Unassigned'}")
            cols[1].write(f"Current category: {txn['category']}")
            cols[2].write(f"Type: {txn.get('transaction_type') or 'expense'}")

            category_index = categories.index(txn["category"]) if txn["category"] in categories else categories.index("Other")
            selected_category = st.selectbox(
                "Category",
                categories,
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
            preview = _rule_preview(conn, user_id, rule_keyword)
            affected_accounts = ", ".join(preview["accounts"]) if preview["accounts"] else "None"
            st.caption(
                f"Rule preview: {preview['count']} uncategorized match(es) across {affected_accounts}. "
                "Already categorized transactions will not be overwritten."
            )
            action_cols = st.columns(2)
            if action_cols[0].button("Save category only", key=f"save_category_{txn['id']}", use_container_width=True):
                _apply_category(conn, user_id, int(txn["id"]), selected_category)
                st.success("Transaction updated.")
                st.rerun()
            if action_cols[1].button(
                "Create rule and categorize",
                key=f"create_rule_{txn['id']}",
                use_container_width=True,
            ):
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


def _render_quick_review(
    conn,
    user_id: int,
    transactions: list[dict],
    categories: list[str],
    *,
    session_key: str,
) -> None:
    skipped = set(st.session_state.get("spending_review_skipped", set()))
    current_ids = {int(txn["id"]) for txn in transactions}

    if st.session_state.get("spending_review_session_key") != session_key:
        st.session_state.spending_review_session_key = session_key
        st.session_state.spending_review_session_ids = current_ids
        skipped = set()
        st.session_state.spending_review_skipped = skipped

    session_ids = set(st.session_state.get("spending_review_session_ids", set())) | current_ids
    st.session_state.spending_review_session_ids = session_ids
    progress = _review_session_progress(session_ids, current_ids, skipped)

    progress_cols = st.columns([1.4, 1, 1, 1])
    progress_cols[0].metric("Review session", f"{progress['completed']} of {progress['total']} complete")
    progress_cols[1].metric("Remaining", progress["remaining"])
    progress_cols[2].metric("Skipped", progress["skipped"])
    if progress_cols[3].button("Reset skips", use_container_width=True, disabled=not progress["skipped"]):
        _clear_review_skips()
        st.rerun()

    completion_ratio = progress["completed"] / progress["total"] if progress["total"] else 1.0
    st.progress(completion_ratio)
    st.caption(
        "Skipped transactions remain uncategorized and can be reviewed later. "
        "Skipping does not delete or exclude a transaction."
    )

    queue = [txn for txn in transactions if int(txn["id"]) not in skipped]
    if not queue:
        st.success("No more transactions remain in this quick review session.")
        return

    page_size_choice = st.selectbox(
        "Transactions shown",
        options=[10, 25, 50, 100, "All"],
        index=0,
        key="spending_review_page_size",
    )
    page_size = len(queue) if page_size_choice == "All" else int(page_size_choice)
    st.caption(f"Showing the oldest {min(page_size, len(queue))} of {len(queue)} remaining transaction(s).")
    for txn in queue[:page_size]:
        _render_review_card(conn, user_id, txn, categories)


def _render_review_card(conn, user_id: int, txn: dict, categories: list[str]) -> None:
    transaction_id = int(txn["id"])
    amount = float(txn["amount"] or 0)
    categories = sorted(categories)
    current_category = txn["category"] if txn["category"] in categories else "Other"
    selected_category = st.session_state.get(f"quick_category_{transaction_id}", current_category)

    with st.container(border=True):
        heading_cols = st.columns([0.8, 3.4, 1])
        heading_cols[0].markdown(f"### {(txn['description'] or 'T')[0].upper()}")
        heading_cols[1].subheader(txn["description"] or "Imported transaction")
        heading_cols[1].caption(f"{txn['date']} · {txn.get('account_name') or 'Unassigned account'}")
        heading_cols[2].markdown(f"### {_format_money(amount)}")
        heading_cols[2].caption(txn["category"])

        category_col, skip_col, rule_col, save_col = st.columns([2.4, 0.8, 1, 1.1])
        selected_category = category_col.selectbox(
            "Category",
            categories,
            index=categories.index(current_category),
            key=f"quick_category_{transaction_id}",
        )
        if skip_col.button("Skip", key=f"quick_skip_{transaction_id}", use_container_width=True):
            _skip_review_transaction(transaction_id)
            st.rerun()
        if rule_col.button("Create rule", key=f"quick_open_rule_{transaction_id}", use_container_width=True):
            st.session_state[f"quick_rule_keyword_{transaction_id}"] = _rule_keyword_from_description(
                txn["description"] or ""
            )
            st.session_state[f"quick_rule_open_{transaction_id}"] = True
            st.rerun()
        if save_col.button(
            "Save category",
            key=f"quick_save_{transaction_id}",
            type="primary",
            use_container_width=True,
        ):
            _apply_category(conn, user_id, transaction_id, selected_category)
            st.rerun()

        suggested_keyword = _rule_keyword_from_description(txn["description"] or "")
        suggestion = _rule_preview(conn, user_id, suggested_keyword)
        if int(suggestion["count"]) >= 2 and not st.session_state.get(f"quick_rule_open_{transaction_id}"):
            st.info(
                f"Suggested rule: merchant contains “{suggested_keyword}”. "
                f"It matches {suggestion['count']} uncategorized transactions."
            )

        if st.session_state.get(f"quick_rule_open_{transaction_id}"):
            _render_rule_preview(conn, user_id, txn, selected_category, categories)


def _render_rule_preview(
    conn,
    user_id: int,
    txn: dict,
    selected_category: str,
    categories: list[str],
) -> None:
    transaction_id = int(txn["id"])
    categories = sorted(categories)
    st.markdown("**Rule preview**")
    rule_col, category_col = st.columns([1.5, 1])
    keyword = rule_col.text_input(
        "Merchant text to match",
        value=_rule_keyword_from_description(txn["description"] or ""),
        key=f"quick_rule_keyword_{transaction_id}",
    )
    rule_category = category_col.selectbox(
        "Category to assign",
        categories,
        index=categories.index(selected_category),
        key=f"quick_rule_category_{transaction_id}",
    )
    preview = _rule_preview(conn, user_id, keyword)
    account_names = ", ".join(preview["accounts"]) if preview["accounts"] else "None"
    st.write(f"Matching transactions: **{preview['count']}**")
    st.write(f"Accounts affected: **{account_names}**")
    st.caption("Only uncategorized matches will change. Already categorized transactions will not be overwritten.")

    apply_existing = st.checkbox(
        "Apply this rule to all matching uncategorized transactions",
        value=True,
        key=f"quick_rule_apply_{transaction_id}",
    )
    action_cols = st.columns([1, 1])
    if action_cols[0].button("Cancel", key=f"quick_rule_cancel_{transaction_id}", use_container_width=True):
        st.session_state[f"quick_rule_open_{transaction_id}"] = False
        st.rerun()
    if action_cols[1].button(
        "Create rule",
        key=f"quick_rule_create_{transaction_id}",
        type="primary",
        use_container_width=True,
        disabled=not keyword.strip(),
    ):
        _create_rule_from_review(
            conn,
            user_id,
            keyword,
            rule_category,
            apply_existing=apply_existing,
        )
        _apply_category(conn, user_id, transaction_id, rule_category)
        st.session_state[f"quick_rule_open_{transaction_id}"] = False
        st.rerun()


def render() -> None:
    user = st.session_state.get("user")
    if not user:
        st.info("Log in to import transactions and review spending.")
        return

    page_header(
        "Spending",
        "Understand where your money goes and clean up imported transactions.",
        action_label="Import CSV",
        on_action=lambda: _navigate_spending("Import"),
    )

    sections = ["Overview", "Accounts", "Transactions", "Cash Flow", "Import"]
    if st.session_state.get("spending_section") not in sections:
        st.session_state.spending_section = "Overview"
    section = st.segmented_control("Spending section", sections, key="spending_section", label_visibility="collapsed")

    user_id = int(user["id"])
    conn = get_connection()
    try:
        summary = get_spending_summary(conn, user_id)
        if section == "Overview":
            _render_overview_section(conn, user_id, summary)
        elif section == "Accounts":
            _render_accounts_section(conn, user_id)
        elif section == "Transactions":
            _render_transaction_review(conn, user_id)
        elif section == "Cash Flow":
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
        elif section == "Import":
            summary = _render_import_section(conn, user_id, summary)
    finally:
        conn.close()
