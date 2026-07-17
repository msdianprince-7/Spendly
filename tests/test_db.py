from database.db import (
    get_category_breakdown,
    get_expense_stats,
    get_expenses_by_user,
    get_user_by_id,
)


def test_get_user_by_id_returns_display_ready_member_since(app, demo_user_id):
    user = get_user_by_id(demo_user_id)
    assert user["name"] == "Demo User"
    assert user["email"] == "demo@spendly.com"
    parts = user["member_since"].split()
    assert len(parts) == 2
    assert parts[1].isdigit()


def test_get_user_by_id_unknown_returns_none(app):
    assert get_user_by_id(999999) is None


def test_get_expenses_by_user_returns_all_seed_rows_newest_first(app, demo_user_id):
    transactions = get_expenses_by_user(demo_user_id)
    assert len(transactions) == 8
    dates = [t["date"] for t in transactions]
    assert dates == sorted(dates, reverse=True)


def test_get_expenses_by_user_empty_for_fresh_user(app, fresh_user_id):
    assert get_expenses_by_user(fresh_user_id) == []


def test_get_expense_stats_for_demo_user(app, demo_user_id):
    stats = get_expense_stats(demo_user_id)
    assert stats["total_spent"] == 798.54
    assert stats["transaction_count"] == 8
    assert stats["top_category"] == "Bills"


def test_get_expense_stats_for_fresh_user(app, fresh_user_id):
    stats = get_expense_stats(fresh_user_id)
    assert stats["total_spent"] == 0
    assert stats["transaction_count"] == 0
    assert stats["top_category"] == "—"


def test_get_category_breakdown_for_demo_user(app, demo_user_id):
    categories = get_category_breakdown(demo_user_id)
    assert len(categories) > 0
    totals = [c["total"] for c in categories]
    assert totals == sorted(totals, reverse=True)
    assert sum(c["percent"] for c in categories) == 100


def test_get_category_breakdown_empty_for_fresh_user(app, fresh_user_id):
    assert get_category_breakdown(fresh_user_id) == []
