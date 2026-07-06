"""Authentication helpers."""

from __future__ import annotations

import sqlite3

import bcrypt

from shared.db import get_connection, row_to_dict
from shared.utils import utc_now_iso


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_user(email: str, password: str, name: str | None = None) -> dict | None:
    conn = get_connection()
    try:
        existing = conn.execute(
            "SELECT id FROM users WHERE email = ?", (email.lower().strip(),)
        ).fetchone()
        if existing:
            return None

        cursor = conn.execute(
            "INSERT INTO users (email, password_hash, name, created_at) VALUES (?, ?, ?, ?)",
            (email.lower().strip(), hash_password(password), name, utc_now_iso()),
        )
        conn.commit()
        return row_to_dict(
            conn.execute("SELECT * FROM users WHERE id = ?", (cursor.lastrowid,)).fetchone()
        )
    finally:
        conn.close()


def authenticate_user(email: str, password: str) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE email = ?", (email.lower().strip(),)
        ).fetchone()
        if not row:
            return None
        user = dict(row)
        if not verify_password(password, user["password_hash"]):
            return None
        user.pop("password_hash", None)
        return user
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute("SELECT id, email, name, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def update_user_profile(user_id: int, *, name: str | None = None) -> dict | None:
    conn = get_connection()
    try:
        conn.execute("UPDATE users SET name = ? WHERE id = ?", (name, user_id))
        conn.commit()
        row = conn.execute("SELECT id, email, name, created_at FROM users WHERE id = ?", (user_id,)).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()


def get_or_create_test_user() -> dict:
    email = "test@financialgps.local"
    password = "test-password-not-for-production"
    existing = get_user_by_email(email)
    if existing:
        return existing
    user = create_user(email, password, "Beta Tester")
    if user is None:
        existing = get_user_by_email(email)
        if existing:
            return existing
        raise RuntimeError("Could not create test user.")
    return user


def get_user_by_email(email: str) -> dict | None:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, email, name, created_at FROM users WHERE email = ?",
            (email.lower().strip(),),
        ).fetchone()
        return row_to_dict(row)
    finally:
        conn.close()
