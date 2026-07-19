from database.db import create_expense, get_expense_by_id, get_expenses_by_user, update_expense
from tests.conftest import login


# --- Unit tests: get_expense_by_id ---

def test_get_expense_by_id_returns_row_for_owner(fresh_user_id):
    expense_id = create_expense(fresh_user_id, 25.0, "Food", "2026-03-20", "Lunch")
    result = get_expense_by_id(expense_id, fresh_user_id)
    assert result is not None
    assert result["amount"] == 25.0
    assert result["category"] == "Food"


def test_get_expense_by_id_returns_none_for_wrong_user(fresh_user_id, demo_user_id):
    expense_id = create_expense(fresh_user_id, 25.0, "Food", "2026-03-20", "Lunch")
    assert get_expense_by_id(expense_id, demo_user_id) is None


def test_get_expense_by_id_returns_none_for_nonexistent_id(fresh_user_id):
    assert get_expense_by_id(99999, fresh_user_id) is None


# --- Unit tests: update_expense ---

def test_update_expense_updates_row_for_owner(fresh_user_id):
    expense_id = create_expense(fresh_user_id, 25.0, "Food", "2026-03-20", "Lunch")
    update_expense(expense_id, fresh_user_id, 99.0, "Transport", "2026-04-01", "Updated")
    updated = get_expense_by_id(expense_id, fresh_user_id)
    assert updated["amount"] == 99.0
    assert updated["category"] == "Transport"
    assert updated["date"] == "2026-04-01"
    assert updated["description"] == "Updated"


def test_update_expense_no_op_for_wrong_user(fresh_user_id, demo_user_id):
    expense_id = create_expense(fresh_user_id, 25.0, "Food", "2026-03-20", "Lunch")
    update_expense(expense_id, demo_user_id, 99.0, "Food", "2026-03-20", "Lunch")
    unchanged = get_expense_by_id(expense_id, fresh_user_id)
    assert unchanged["amount"] == 25.0


# --- Route tests: GET ---

def test_edit_expense_get_redirects_when_not_logged_in(client, fresh_user_id):
    expense_id = create_expense(fresh_user_id, 25.0, "Food", "2026-03-20", "Lunch")
    response = client.get(f"/expenses/{expense_id}/edit")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_edit_expense_get_returns_200_prefilled_for_owner(client, fresh_user_id):
    login(client, fresh_user_id, name="Fresh User")
    expense_id = create_expense(fresh_user_id, 25.0, "Food", "2026-03-20", "Lunch")
    response = client.get(f"/expenses/{expense_id}/edit")
    body = response.data.decode()
    assert response.status_code == 200
    assert "<form" in body
    assert 'value="25.0"' in body
    assert 'value="2026-03-20"' in body
    assert '<option value="Food" selected>' in body
    assert 'value="Lunch"' in body


def test_edit_expense_get_404_for_other_users_expense(client, fresh_user_id, demo_user_id):
    login(client, demo_user_id)
    expense_id = create_expense(fresh_user_id, 25.0, "Food", "2026-03-20", "Lunch")
    response = client.get(f"/expenses/{expense_id}/edit")
    assert response.status_code == 404


def test_edit_expense_get_404_for_nonexistent_id(client, demo_user_id):
    login(client, demo_user_id)
    response = client.get("/expenses/99999/edit")
    assert response.status_code == 404


# --- Route tests: POST ---

def test_edit_expense_post_redirects_when_not_logged_in(client, fresh_user_id):
    expense_id = create_expense(fresh_user_id, 25.0, "Food", "2026-03-20", "Lunch")
    response = client.post(
        f"/expenses/{expense_id}/edit",
        data={"amount": "10", "category": "Food", "date": "2026-03-20"},
    )
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_edit_expense_post_valid_data_redirects_and_updates(client, fresh_user_id):
    login(client, fresh_user_id, name="Fresh User")
    expense_id = create_expense(fresh_user_id, 25.0, "Food", "2026-03-20", "Lunch")
    response = client.post(
        f"/expenses/{expense_id}/edit",
        data={"amount": "99.0", "category": "Transport", "date": "2026-04-01", "description": "Updated"},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")

    updated = get_expense_by_id(expense_id, fresh_user_id)
    assert updated["amount"] == 99.0
    assert updated["category"] == "Transport"
    assert updated["date"] == "2026-04-01"
    assert updated["description"] == "Updated"


def test_edit_expense_post_404_for_other_users_expense(client, fresh_user_id, demo_user_id):
    login(client, demo_user_id)
    expense_id = create_expense(fresh_user_id, 25.0, "Food", "2026-03-20", "Lunch")
    response = client.post(
        f"/expenses/{expense_id}/edit",
        data={"amount": "99.0", "category": "Food", "date": "2026-03-20"},
    )
    assert response.status_code == 404

    unchanged = get_expense_by_id(expense_id, fresh_user_id)
    assert unchanged["amount"] == 25.0


def test_edit_expense_post_missing_amount_rerenders_with_error(client, fresh_user_id):
    login(client, fresh_user_id, name="Fresh User")
    expense_id = create_expense(fresh_user_id, 25.0, "Food", "2026-03-20", "Lunch")
    response = client.post(
        f"/expenses/{expense_id}/edit",
        data={"amount": "", "category": "Food", "date": "2026-03-20"},
    )
    body = response.data.decode()
    assert response.status_code == 200
    assert "auth-error" in body
    assert "Amount must be" in body
    assert get_expense_by_id(expense_id, fresh_user_id)["amount"] == 25.0


def test_edit_expense_post_zero_amount_rerenders_with_error(client, fresh_user_id):
    login(client, fresh_user_id, name="Fresh User")
    expense_id = create_expense(fresh_user_id, 25.0, "Food", "2026-03-20", "Lunch")
    response = client.post(
        f"/expenses/{expense_id}/edit",
        data={"amount": "0", "category": "Food", "date": "2026-03-20"},
    )
    body = response.data.decode()
    assert response.status_code == 200
    assert "Amount must be greater than 0" in body
    assert get_expense_by_id(expense_id, fresh_user_id)["amount"] == 25.0


def test_edit_expense_post_non_numeric_amount_rerenders_with_error(client, fresh_user_id):
    login(client, fresh_user_id, name="Fresh User")
    expense_id = create_expense(fresh_user_id, 25.0, "Food", "2026-03-20", "Lunch")
    response = client.post(
        f"/expenses/{expense_id}/edit",
        data={"amount": "abc", "category": "Food", "date": "2026-03-20"},
    )
    body = response.data.decode()
    assert response.status_code == 200
    assert "Amount must be a valid number" in body
    assert get_expense_by_id(expense_id, fresh_user_id)["amount"] == 25.0


def test_edit_expense_post_invalid_category_rerenders_with_error(client, fresh_user_id):
    login(client, fresh_user_id, name="Fresh User")
    expense_id = create_expense(fresh_user_id, 25.0, "Food", "2026-03-20", "Lunch")
    response = client.post(
        f"/expenses/{expense_id}/edit",
        data={"amount": "10", "category": "Crypto", "date": "2026-03-20"},
    )
    body = response.data.decode()
    assert response.status_code == 200
    assert "Please select a valid category" in body
    assert get_expense_by_id(expense_id, fresh_user_id)["category"] == "Food"


def test_edit_expense_post_invalid_date_rerenders_with_error(client, fresh_user_id):
    login(client, fresh_user_id, name="Fresh User")
    expense_id = create_expense(fresh_user_id, 25.0, "Food", "2026-03-20", "Lunch")
    response = client.post(
        f"/expenses/{expense_id}/edit",
        data={"amount": "10", "category": "Food", "date": "not-a-date"},
    )
    body = response.data.decode()
    assert response.status_code == 200
    assert "Please enter a valid date" in body
    assert get_expense_by_id(expense_id, fresh_user_id)["date"] == "2026-03-20"


def test_edit_expense_post_no_description_saves_null(client, fresh_user_id):
    login(client, fresh_user_id, name="Fresh User")
    expense_id = create_expense(fresh_user_id, 25.0, "Food", "2026-03-20", "Lunch")
    response = client.post(
        f"/expenses/{expense_id}/edit",
        data={"amount": "10", "category": "Food", "date": "2026-03-20", "description": ""},
    )
    assert response.status_code == 302
    updated = get_expense_by_id(expense_id, fresh_user_id)
    assert updated["description"] is None
