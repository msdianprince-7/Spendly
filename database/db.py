import sqlite3
from datetime import date, datetime
from pathlib import Path

from werkzeug.security import generate_password_hash

DB_PATH = Path(__file__).resolve().parent.parent / "expense_tracker.db"

CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.commit()
    conn.close()


def create_user(name, email, password_hash):
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_user_by_email(email):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM users WHERE LOWER(email) = LOWER(?)",
            (email,),
        ).fetchone()
    finally:
        conn.close()


def get_user_by_id(user_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if row is None:
            return None
        user = dict(row)
        created = datetime.strptime(user["created_at"], "%Y-%m-%d %H:%M:%S")
        user["member_since"] = created.strftime("%B %Y")
        return user
    finally:
        conn.close()


def create_expense(user_id, amount, category, date, description):
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date, description),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def seed_db():
    conn = get_db()
    existing = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()
    if existing["count"] > 0:
        conn.close()
        return

    password_hash = generate_password_hash("demo123")
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Demo User", "demo@spendly.com", password_hash),
    )
    user_id = cursor.lastrowid

    today = date.today()
    sample_expenses = [
        (12.50, "Food", today.replace(day=2).isoformat(), "Grocery run"),
        (8.75, "Transport", today.replace(day=3).isoformat(), "Bus fare"),
        (45.00, "Bills", today.replace(day=5).isoformat(), "Electricity bill"),
        (650.00, "Bills", today.replace(day=6).isoformat(), "Monthly rent"),
        (22.30, "Health", today.replace(day=10).isoformat(), "Pharmacy"),
        (15.00, "Entertainment", today.replace(day=14).isoformat(), "Movie tickets"),
        (39.99, "Shopping", today.replace(day=18).isoformat(), "New shoes"),
        (5.00, "Other", today.replace(day=22).isoformat(), "Miscellaneous"),
    ]
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        [(user_id, amt, cat, dt, desc) for amt, cat, dt, desc in sample_expenses],
    )
    conn.commit()
    conn.close()


def _date_range_clause(user_id, start_date, end_date):
    conditions = ["user_id = ?"]
    params = [user_id]
    if start_date is not None:
        conditions.append("date >= ?")
        params.append(start_date)
    if end_date is not None:
        conditions.append("date <= ?")
        params.append(end_date)
    return " AND ".join(conditions), params


def get_expenses_by_user(user_id, start_date=None, end_date=None):
    conn = get_db()
    try:
        where, params = _date_range_clause(user_id, start_date, end_date)
        rows = conn.execute(
            f"SELECT id, amount, category, date, description "
            f"FROM expenses WHERE {where} ORDER BY date DESC, id DESC",
            params,
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_expense_stats(user_id, start_date=None, end_date=None):
    conn = get_db()
    try:
        where, params = _date_range_clause(user_id, start_date, end_date)
        total_row = conn.execute(
            f"SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS count "
            f"FROM expenses WHERE {where}",
            params,
        ).fetchone()
        top_row = conn.execute(
            f"SELECT category, SUM(amount) AS cat_total "
            f"FROM expenses WHERE {where} "
            f"GROUP BY category ORDER BY cat_total DESC LIMIT 1",
            params,
        ).fetchone()
        return {
            "total_spent": float(total_row["total"]),
            "transaction_count": int(total_row["count"]),
            "top_category": top_row["category"] if top_row else "—",
        }
    finally:
        conn.close()


def get_category_breakdown(user_id, start_date=None, end_date=None):
    conn = get_db()
    try:
        where, params = _date_range_clause(user_id, start_date, end_date)
        rows = conn.execute(
            f"SELECT category AS name, SUM(amount) AS total "
            f"FROM expenses WHERE {where} "
            f"GROUP BY category ORDER BY total DESC",
            params,
        ).fetchall()
        categories = [{"name": r["name"], "total": float(r["total"])} for r in rows]
        if not categories:
            return []

        grand_total = sum(c["total"] for c in categories)
        percents = [round(c["total"] / grand_total * 100) for c in categories]
        drift = 100 - sum(percents)
        percents[0] += drift
        for c, p in zip(categories, percents):
            c["percent"] = p
        return categories
    finally:
        conn.close()
