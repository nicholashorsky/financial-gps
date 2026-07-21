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
    """Normalize accents, punctuation, and whitespace for reliable rule matching."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", " ", text.lower())
    return " ".join(text.split())


def load_user_rules(conn: sqlite3.Connection, user_id: int) -> list[CategoryRule]:
    rows = conn.execute(
        """
        SELECT keyword, category, priority, source
        FROM category_rules
        WHERE user_id = ? AND is_enabled = 1
        ORDER BY priority DESC, id ASC
        """,
        (user_id,),
    ).fetchall()
    return [
        CategoryRule(keyword=r["keyword"], category=r["category"], priority=r["priority"], source=r["source"])
        for r in rows
    ]


def get_all_rules(conn: sqlite3.Connection | None, user_id: int | None) -> list[CategoryRule]:
    if conn and user_id:
        seed_system_rules(conn, user_id)
        enabled_categories = set(get_user_categories(conn, user_id))
        user_rules = [rule for rule in load_user_rules(conn, user_id) if rule.category in enabled_categories]
        # User rules win — prepend with boosted priority
        for ur in user_rules:
            if ur.source == "user":
                ur.priority = ur.priority + 1000
        return sorted(user_rules, key=lambda r: -r.priority)
    rules = [CategoryRule(keyword=k, category=c, priority=p, source="system") for k, c, p in SYSTEM_KEYWORDS]
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
        if normalize_text(rule.keyword) in normalized:
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


def seed_user_categories(conn: sqlite3.Connection, user_id: int) -> int:
    inserted = 0
    for category in CATEGORIES:
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO user_categories (user_id, name, is_default, is_enabled)
            VALUES (?, ?, 1, 1)
            """,
            (user_id, category),
        )
        inserted += int(cursor.rowcount or 0)
    conn.commit()
    return inserted


def list_user_categories(conn: sqlite3.Connection, user_id: int, *, enabled_only: bool = False) -> list[sqlite3.Row]:
    seed_user_categories(conn, user_id)
    enabled_filter = "AND is_enabled = 1" if enabled_only else ""
    return conn.execute(
        f"""
        SELECT id, name, is_default, is_enabled
        FROM user_categories
        WHERE user_id = ? {enabled_filter}
        ORDER BY is_default DESC, name ASC
        """,
        (user_id,),
    ).fetchall()


def get_user_categories(conn: sqlite3.Connection, user_id: int) -> list[str]:
    return [str(row["name"]) for row in list_user_categories(conn, user_id, enabled_only=True)]


def add_user_category(conn: sqlite3.Connection, user_id: int, name: str) -> int:
    clean_name = " ".join(name.strip().split())
    if not clean_name:
        raise ValueError("Category name is required.")
    existing = conn.execute(
        "SELECT id FROM user_categories WHERE user_id = ? AND lower(name) = lower(?)",
        (user_id, clean_name),
    ).fetchone()
    if existing:
        raise ValueError("That category already exists.")
    cursor = conn.execute(
        "INSERT INTO user_categories (user_id, name, is_default, is_enabled) VALUES (?, ?, 0, 1)",
        (user_id, clean_name),
    )
    conn.commit()
    return int(cursor.lastrowid)


def set_category_enabled(conn: sqlite3.Connection, user_id: int, category_id: int, enabled: bool) -> bool:
    row = conn.execute(
        "SELECT name FROM user_categories WHERE id = ? AND user_id = ?",
        (category_id, user_id),
    ).fetchone()
    if not row:
        return False
    if row["name"] == "Other" and not enabled:
        raise ValueError("The Other category must remain enabled as a fallback.")
    conn.execute(
        "UPDATE user_categories SET is_enabled = ? WHERE id = ? AND user_id = ?",
        (int(enabled), category_id, user_id),
    )
    conn.commit()
    return True


def rename_user_category(conn: sqlite3.Connection, user_id: int, category_id: int, name: str) -> bool:
    clean_name = " ".join(name.strip().split())
    if not clean_name:
        raise ValueError("Category name is required.")
    row = conn.execute(
        "SELECT name, is_default FROM user_categories WHERE id = ? AND user_id = ?",
        (category_id, user_id),
    ).fetchone()
    if not row:
        return False
    if row["is_default"]:
        raise ValueError("Default categories can be disabled but not renamed.")
    in_use = conn.execute(
        "SELECT COUNT(*) FROM transactions WHERE user_id = ? AND category = ?",
        (user_id, row["name"]),
    ).fetchone()[0]
    if in_use:
        raise ValueError("This category is in use. Disable it or move its transactions before renaming it.")
    conn.execute(
        "UPDATE user_categories SET name = ? WHERE id = ? AND user_id = ?",
        (clean_name, category_id, user_id),
    )
    conn.commit()
    return True


def add_user_rule(
    conn: sqlite3.Connection,
    user_id: int,
    keyword: str,
    category: str,
    priority: int = 50,
) -> int:
    """Insert a user-defined category rule."""

    keyword = normalize_text(keyword)
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


def update_user_rule(
    conn: sqlite3.Connection,
    rule_id: int,
    user_id: int,
    keyword: str,
    category: str,
    priority: int,
) -> bool:
    clean_keyword = normalize_text(keyword)
    if not clean_keyword or not category.strip():
        raise ValueError("Keyword and category are required.")
    cursor = conn.execute(
        """
        UPDATE category_rules SET keyword = ?, category = ?, priority = ?
        WHERE id = ? AND user_id = ? AND source = 'user'
        """,
        (clean_keyword, category.strip(), priority, rule_id, user_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def count_rule_matches(conn: sqlite3.Connection, user_id: int, keyword: str) -> int:
    normalized_keyword = normalize_text(keyword)
    if not normalized_keyword:
        return 0
    rows = conn.execute(
        "SELECT description FROM transactions WHERE user_id = ?",
        (user_id,),
    ).fetchall()
    return sum(normalized_keyword in normalize_text(row["description"] or "") for row in rows)


def set_rule_enabled(conn: sqlite3.Connection, rule_id: int, user_id: int, enabled: bool) -> bool:
    cursor = conn.execute(
        "UPDATE category_rules SET is_enabled = ? WHERE id = ? AND user_id = ?",
        (int(enabled), rule_id, user_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def list_category_rules(conn: sqlite3.Connection, user_id: int) -> list[tuple[int, str, str, int, str, bool]]:
    """Return category rules for display in the UI."""

    rows = conn.execute(
        """
        SELECT id, keyword, category, priority, source, is_enabled
        FROM category_rules
        WHERE user_id = ?
        ORDER BY CASE WHEN source = 'user' THEN 0 ELSE 1 END, priority DESC, keyword ASC
        """,
        (user_id,),
    ).fetchall()
    return [
        (int(r["id"]), r["keyword"], r["category"], int(r["priority"] or 0), r["source"], bool(r["is_enabled"]))
        for r in rows
    ]
