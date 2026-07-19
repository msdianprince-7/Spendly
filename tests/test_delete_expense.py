from database.db import create_expense, delete_expense, get_expense_by_id
from tests.conftest import login


# --- Unit tests: delete_expense ---

def test_delete_expense_removes_row_for_owner(fresh_user_id):
    expense_id = create_expense(fresh_user_id, 25.0, "Food", "2026-03-20", "Lunch")
    delete_expense(expense_id, fresh_user_id)
    assert get_expense_by_id(expense_id, fresh_user_id) is None


def test_delete_expense_no_op_for_wrong_user(fresh_user_id, demo_user_id):
    expense_id = create_expense(fresh_user_id, 25.0, "Food", "2026-03-20", "Lunch")
    delete_expense(expense_id, demo_user_id)
    assert get_expense_by_id(expense_id, fresh_user_id) is not None


def test_delete_expense_no_op_for_nonexistent_id(fresh_user_id):
    delete_expense(99999, fresh_user_id)


# --- Route tests: POST ---

def test_delete_expense_post_redirects_when_not_logged_in(client, fresh_user_id):
    expense_id = create_expense(fresh_user_id, 25.0, "Food", "2026-03-20", "Lunch")
    response = client.post(f"/expenses/{expense_id}/delete")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_delete_expense_post_removes_and_redirects_for_owner(client, fresh_user_id):
    login(client, fresh_user_id, name="Fresh User")
    expense_id = create_expense(fresh_user_id, 25.0, "Food", "2026-03-20", "Lunch")
    response = client.post(f"/expenses/{expense_id}/delete")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")
    assert get_expense_by_id(expense_id, fresh_user_id) is None


def test_delete_expense_post_404_for_other_users_expense(client, fresh_user_id, demo_user_id):
    login(client, demo_user_id)
    expense_id = create_expense(fresh_user_id, 25.0, "Food", "2026-03-20", "Lunch")
    response = client.post(f"/expenses/{expense_id}/delete")
    assert response.status_code == 404
    assert get_expense_by_id(expense_id, fresh_user_id) is not None


def test_delete_expense_post_404_for_nonexistent_id(client, demo_user_id):
    login(client, demo_user_id)
    response = client.post("/expenses/99999/delete")
    assert response.status_code == 404


# --- Route tests: GET ---

def test_delete_expense_get_returns_405(client, fresh_user_id):
    login(client, fresh_user_id, name="Fresh User")
    expense_id = create_expense(fresh_user_id, 25.0, "Food", "2026-03-20", "Lunch")
    response = client.get(f"/expenses/{expense_id}/delete")
    assert response.status_code == 405
