from tests.conftest import login


def test_profile_redirects_when_not_logged_in(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_returns_200_when_logged_in(client, demo_user_id):
    login(client, demo_user_id)
    response = client.get("/profile")
    assert response.status_code == 200


def test_profile_shows_demo_user_data(client, demo_user_id):
    login(client, demo_user_id)
    body = client.get("/profile").data.decode()
    assert "Demo User" in body
    assert "demo@spendly.com" in body
    assert "798.54" in body
    assert "Bills" in body
    assert "₹" in body


def test_profile_empty_state_for_fresh_user(client, fresh_user_id):
    login(client, fresh_user_id, name="Fresh User")
    body = client.get("/profile").data.decode()
    assert "0.00" in body
    assert "profile-badge-" not in body
