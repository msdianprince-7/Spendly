import sys

import pytest

import database.db as db_module


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(db_module, "DB_PATH", tmp_path / "test.db")

    sys.modules.pop("app", None)
    import app as app_module

    app_module.app.config["TESTING"] = True
    yield app_module.app

    sys.modules.pop("app", None)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def demo_user_id(app):
    from database.db import get_user_by_email

    return get_user_by_email("demo@spendly.com")["id"]


@pytest.fixture
def fresh_user_id(app):
    from werkzeug.security import generate_password_hash

    from database.db import create_user

    return create_user(
        "Fresh User", "fresh@example.com", generate_password_hash("password123")
    )


def login(client, user_id, name="Demo User"):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["name"] = name
