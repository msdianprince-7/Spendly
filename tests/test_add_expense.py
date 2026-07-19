from database.db import get_expenses_by_user
from tests.conftest import login


def test_add_expense_get_redirects_when_not_logged_in(client):
    response = client.get("/expenses/add")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_add_expense_post_redirects_when_not_logged_in(client):
    response = client.post("/expenses/add", data={"amount": "10", "category": "Food", "date": "2026-03-20"})
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_add_expense_get_returns_200_when_logged_in(client, demo_user_id):
    login(client, demo_user_id)
    response = client.get("/expenses/add")
    body = response.data.decode()
    assert response.status_code == 200
    assert "<form" in body
    for category in ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]:
        assert category in body


def test_add_expense_post_valid_data_redirects_and_inserts(client, fresh_user_id):
    login(client, fresh_user_id, name="Fresh User")
    response = client.post(
        "/expenses/add",
        data={"amount": "50.0", "category": "Food", "date": "2026-03-20", "description": "Lunch"},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")

    transactions = get_expenses_by_user(fresh_user_id)
    assert len(transactions) == 1
    assert transactions[0]["amount"] == 50.0
    assert transactions[0]["category"] == "Food"
    assert transactions[0]["date"] == "2026-03-20"
    assert transactions[0]["description"] == "Lunch"


def test_add_expense_post_no_description_saves_null(client, fresh_user_id):
    login(client, fresh_user_id, name="Fresh User")
    response = client.post(
        "/expenses/add",
        data={"amount": "12.0", "category": "Transport", "date": "2026-03-20", "description": ""},
    )
    assert response.status_code == 302

    transactions = get_expenses_by_user(fresh_user_id)
    assert len(transactions) == 1
    assert transactions[0]["description"] is None


def test_add_expense_post_missing_amount_rerenders_with_error(client, fresh_user_id):
    login(client, fresh_user_id, name="Fresh User")
    response = client.post(
        "/expenses/add",
        data={"amount": "", "category": "Food", "date": "2026-03-20"},
    )
    body = response.data.decode()
    assert response.status_code == 200
    assert "auth-error" in body
    assert "Amount must be" in body
    assert get_expenses_by_user(fresh_user_id) == []


def test_add_expense_post_zero_amount_rerenders_with_error(client, fresh_user_id):
    login(client, fresh_user_id, name="Fresh User")
    response = client.post(
        "/expenses/add",
        data={"amount": "0", "category": "Food", "date": "2026-03-20"},
    )
    body = response.data.decode()
    assert response.status_code == 200
    assert "auth-error" in body
    assert "Amount must be greater than 0" in body
    assert get_expenses_by_user(fresh_user_id) == []


def test_add_expense_post_non_numeric_amount_rerenders_with_error(client, fresh_user_id):
    login(client, fresh_user_id, name="Fresh User")
    response = client.post(
        "/expenses/add",
        data={"amount": "abc", "category": "Food", "date": "2026-03-20"},
    )
    body = response.data.decode()
    assert response.status_code == 200
    assert "auth-error" in body
    assert "Amount must be a valid number" in body
    assert get_expenses_by_user(fresh_user_id) == []


def test_add_expense_post_invalid_category_rerenders_with_error(client, fresh_user_id):
    login(client, fresh_user_id, name="Fresh User")
    response = client.post(
        "/expenses/add",
        data={"amount": "10", "category": "Crypto", "date": "2026-03-20"},
    )
    body = response.data.decode()
    assert response.status_code == 200
    assert "auth-error" in body
    assert "Please select a valid category" in body
    assert get_expenses_by_user(fresh_user_id) == []


def test_add_expense_post_invalid_date_rerenders_with_error(client, fresh_user_id):
    login(client, fresh_user_id, name="Fresh User")
    response = client.post(
        "/expenses/add",
        data={"amount": "10", "category": "Food", "date": "not-a-date"},
    )
    body = response.data.decode()
    assert response.status_code == 200
    assert "auth-error" in body
    assert "Please enter a valid date" in body
    assert get_expenses_by_user(fresh_user_id) == []
