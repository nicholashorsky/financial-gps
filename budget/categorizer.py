"""Transaction categorization via keyword rules."""

from __future__ import annotations

import re
import sqlite3
import unicodedata
from dataclasses import dataclass

from budget.models import CategorizedTransaction, ParsedTransaction

CATEGORIES = [
    "Housing",
    "Utilities",
    "Groceries",
    "Dining",
    "Transportation",
    "Entertainment",
    "Shopping",
    "Health",
    "Insurance",
    "Subscriptions",
    "Travel",
    "Education",
    "Personal Care",
    "Gifts",
    "Fees",
    "Income",
    "Transfer",
    "Other",
]

# 50+ keyword rules: (keyword, category, priority)
SYSTEM_KEYWORDS: list[tuple[str, str, int]] = [
    # Housing
    ("rent", "Housing", 10),
    ("mortgage", "Housing", 10),
    ("property tax", "Housing", 10),
    ("condo fee", "Housing", 10),
    ("home depot", "Housing", 8),
    ("ikea", "Housing", 5),
    # Utilities
    ("hydro", "Utilities", 10),
    ("enbridge", "Utilities", 10),
    ("bell", "Utilities", 8),
    ("rogers", "Utilities", 8),
    ("telus", "Utilities", 8),
    ("fido", "Utilities", 8),
    ("koodo", "Utilities", 8),
    ("internet", "Utilities", 8),
    ("electric", "Utilities", 8),
    ("water bill", "Utilities", 10),
    # Groceries
    ("loblaws", "Groceries", 10),
    ("metro", "Groceries", 8),
    ("sobeys", "Groceries", 10),
    ("costco", "Groceries", 8),
    ("walmart", "Groceries", 6),
    ("no frills", "Groceries", 10),
    ("freshco", "Groceries", 10),
    ("food basics", "Groceries", 10),
    ("farm boy", "Groceries", 10),
    ("whole foods", "Groceries", 10),
    ("t&t", "Groceries", 10),
    # Dining
    ("restaurant", "Dining", 10),
    ("tim hortons", "Dining", 10),
    ("starbucks", "Dining", 10),
    ("mcdonald", "Dining", 10),
    ("uber eats", "Dining", 10),
    ("doordash", "Dining", 10),
    ("skip the dishes", "Dining", 10),
    ("pizza", "Dining", 8),
    ("cafe", "Dining", 8),
    ("pub", "Dining", 8),
    # Transportation
    ("presto", "Transportation", 10),
    ("gas bar", "Transportation", 10),
    ("petro", "Transportation", 10),
    ("shell", "Transportation", 8),
    ("esso", "Transportation", 10),
    ("parking", "Transportation", 10),
    ("uber", "Transportation", 8),
    ("lyft", "Transportation", 10),
    ("go transit", "Transportation", 10),
    ("ttc", "Transportation", 10),
    # Entertainment
    ("netflix", "Entertainment", 10),
    ("spotify", "Entertainment", 10),
    ("cinema", "Entertainment", 10),
    ("ticketmaster", "Entertainment", 10),
    ("steam", "Entertainment", 10),
    ("playstation", "Entertainment", 10),
    # Shopping
    ("amazon", "Shopping", 10),
    ("amazon.ca", "Shopping", 10),
    ("best buy", "Shopping", 10),
    ("canadian tire", "Shopping", 10),
    ("winners", "Shopping", 10),
    ("indigo", "Shopping", 10),
    # Health
    ("pharmacy", "Health", 10),
    ("shoppers drug", "Health", 10),
    ("rexall", "Health", 10),
    ("dental", "Health", 10),
    ("physio", "Health", 10),
    ("hospital", "Health", 10),
    # Insurance
    ("insurance", "Insurance", 10),
    ("manulife", "Insurance", 10),
    ("sun life", "Insurance", 10),
    # Subscriptions
    ("subscription", "Subscriptions", 10),
    ("adobe", "Subscriptions", 10),
    ("microsoft 365", "Subscriptions", 10),
    ("icloud", "Subscriptions", 10),
    ("google storage", "Subscriptions", 10),
    ("gym", "Subscriptions", 10),
    ("goodlife", "Subscriptions", 10),
    # Travel
    ("air canada", "Travel", 10),
    ("westjet", "Travel", 10),
    ("expedia", "Travel", 10),
    ("hotel", "Travel", 8),
    ("airbnb", "Travel", 10),
    # Education
    ("tuition", "Education", 10),
    ("university", "Education", 8),
    ("college", "Education", 8),
    ("udemy", "Education", 10),
    # Personal Care
    ("salon", "Personal Care", 10),
    ("barber", "Personal Care", 10),
    ("sephora", "Personal Care", 10),
    # Gifts
    ("gift", "Gifts", 8),
    # Fees
    ("service charge", "Fees", 10),
    ("bank fee", "Fees", 10),
    ("overdraft", "Fees", 10),
    ("interest charge", "Fees", 10),
    # Income
    ("payroll", "Income", 10),
    ("direct deposit", "Income", 10),
    ("salary", "Income", 10),
    ("deposit", "Income", 5),
    ("e-transfer received", "Income", 10),
    ("refund", "Income", 8),
    # Transfer
    ("e-transfer sent", "Transfer", 10),
    ("transfer to", "Transfer", 10),
    ("transfer from", "Transfer", 10),
    ("payment to rbc", "Transfer", 10),
    ("payment received", "Transfer", 10),
    ("visa payment", "Transfer", 10),
    ("mastercard payment", "Transfer", 10),
    ("bill payment", "Transfer", 8),
]


@dataclass
class CategoryRule:
    keyword: str
    category: str
    priority: int
    source: str = "system"


def normalize_text(text: str) -> str:
    """Strip accents and lowercase for matching (handles French RBC descriptions)."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    return text.lower().strip()


def load_user_rules(conn: sqlite3.Connection, user_id: int) -> list[CategoryRule]:
    rows = conn.execute(
        """
        SELECT keyword, category, priority, source
        FROM category_rules
        WHERE user_id = ?
        ORDER BY priority DESC, id ASC
        """,
        (user_id,),
    ).fetchall()
    return [
        CategoryRule(keyword=r["keyword"], category=r["category"], priority=r["priority"], source=r["source"])
        for r in rows
    ]


def get_all_rules(conn: sqlite3.Connection | None, user_id: int | None) -> list[CategoryRule]:
    rules = [
        CategoryRule(keyword=k, category=c, priority=p, source="system")
        for k, c, p in SYSTEM_KEYWORDS
    ]
    if conn and user_id:
        user_rules = load_user_rules(conn, user_id)
        # User rules win — prepend with boosted priority
        for ur in user_rules:
            ur.priority = ur.priority + 1000
        rules = user_rules + rules
    return sorted(rules, key=lambda r: -r.priority)


def infer_transaction_type(amount: float, category: str, description: str) -> str:
    desc = normalize_text(description)
    if category == "Income" or amount > 0:
        if any(k in desc for k in ("payment received", "payment to rbc", "visa payment", "transfer to")):
            return "transfer_out" if amount < 0 else "transfer_in"
        if "payment received" in desc and amount > 0:
            return "cc_payment"
        return "income"
    if category == "Transfer":
        if "payment received" in desc:
            return "cc_payment"
        if amount < 0:
            return "transfer_out"
        return "transfer_in"
    return "expense"


def categorize_description(
    description: str,
    amount: float,
    rules: list[CategoryRule] | None = None,
) -> tuple[str, str]:
    """Return (category, transaction_type) for a description."""
    rules = rules or [
        CategoryRule(keyword=k, category=c, priority=p, source="system")
        for k, c, p in SYSTEM_KEYWORDS
    ]
    normalized = normalize_text(description)

    for rule in rules:
        if rule.keyword in normalized:
            txn_type = infer_transaction_type(amount, rule.category, description)
            return rule.category, txn_type

    txn_type = "income" if amount > 0 else "expense"
    return "Uncategorized", txn_type


def categorize_transactions(
    transactions: list[ParsedTransaction],
    conn: sqlite3.Connection | None = None,
    user_id: int | None = None,
) -> list[CategorizedTransaction]:
    rules = get_all_rules(conn, user_id)
    results = []
    for txn in transactions:
        category, txn_type = categorize_description(txn.description, txn.amount, rules)
        results.append(
            CategorizedTransaction(
                date=txn.date,
                description=txn.description,
                amount=txn.amount,
                category=category,
                transaction_type=txn_type,
                raw_description=txn.raw_description,
                account_key=txn.account_hint,
            )
        )
    return results


def seed_system_rules(conn: sqlite3.Connection, user_id: int) -> int:
    """Insert system keyword rules for a user if none exist."""
    count = conn.execute(
        "SELECT COUNT(*) FROM category_rules WHERE user_id = ? AND source = 'system'",
        (user_id,),
    ).fetchone()[0]
    if count > 0:
        return 0

    inserted = 0
    for keyword, category, priority in SYSTEM_KEYWORDS:
        conn.execute(
            """
            INSERT INTO category_rules (user_id, keyword, category, priority, source)
            VALUES (?, ?, ?, ?, 'system')
            """,
            (user_id, keyword, category, priority),
        )
        inserted += 1
    conn.commit()
    return inserted


def add_user_rule(
    conn: sqlite3.Connection,
    user_id: int,
    keyword: str,
    category: str,
    priority: int = 50,
) -> int:
    """Insert a user-defined category rule."""

    keyword = keyword.strip().lower()
    category = category.strip()
    if not keyword or not category:
        raise ValueError("Keyword and category are required.")

    cursor = conn.execute(
        """
        INSERT INTO category_rules (user_id, keyword, category, priority, source)
        VALUES (?, ?, ?, ?, 'user')
        """,
        (user_id, keyword, category, priority),
    )
    conn.commit()
    return int(cursor.lastrowid)


def delete_user_rule(conn: sqlite3.Connection, rule_id: int, user_id: int) -> None:
    """Delete a user rule if it belongs to the current user."""

    conn.execute(
        "DELETE FROM category_rules WHERE id = ? AND user_id = ? AND source = 'user'",
        (rule_id, user_id),
    )
    conn.commit()


def list_category_rules(conn: sqlite3.Connection, user_id: int) -> list[tuple[int, str, str, int, str]]:
    """Return category rules for display in the UI."""

    rows = conn.execute(
        """
        SELECT id, keyword, category, priority, source
        FROM category_rules
        WHERE user_id = ?
        ORDER BY CASE WHEN source = 'user' THEN 0 ELSE 1 END, priority DESC, keyword ASC
        """,
        (user_id,),
    ).fetchall()
    return [(int(r["id"]), r["keyword"], r["category"], int(r["priority"] or 0), r["source"]) for r in rows]
