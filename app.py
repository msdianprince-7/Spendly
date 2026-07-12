import os

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import create_user, get_db, get_user_by_email, init_db, seed_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-fallback-key")

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #


@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not name or not email or not password:
            error = "All fields are required."
        elif len(password) < 8:
            error = "Password must be at least 8 characters long."
        else:
            password_hash = generate_password_hash(password)
            user_id = create_user(name, email, password_hash)
            if user_id is None:
                error = "An account with that email already exists."
            else:
                return redirect(url_for("login"))

        return render_template("register.html", error=error, name=name, email=email)

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("profile"))

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email or not password:
            error = "Invalid email or password."
        else:
            user = get_user_by_email(email)
            if user is None or not check_password_hash(user["password_hash"], password):
                error = "Invalid email or password."
            else:
                session.clear()
                session["user_id"] = user["id"]
                session["name"] = user["name"]
                return redirect(url_for("profile"))

        return render_template("login.html", error=error)

    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")



# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = {
        "name": session.get("name"),
        "email": "demo@spendly.com",
        "member_since": "January 2026",
    }

    stats = {
        "total_spent": 798.54,
        "transaction_count": 8,
        "top_category": "Bills",
    }

    transactions = [
        {"date": "2026-07-06", "description": "Monthly rent", "category": "Bills", "amount": 650.00},
        {"date": "2026-07-05", "description": "Electricity bill", "category": "Bills", "amount": 45.00},
        {"date": "2026-07-18", "description": "New shoes", "category": "Shopping", "amount": 39.99},
        {"date": "2026-07-10", "description": "Pharmacy", "category": "Health", "amount": 22.30},
        {"date": "2026-07-14", "description": "Movie tickets", "category": "Entertainment", "amount": 15.00},
    ]

    categories = [
        {"name": "Bills", "total": 695.00, "percent": 87},
        {"name": "Shopping", "total": 39.99, "percent": 5},
        {"name": "Health", "total": 22.30, "percent": 3},
        {"name": "Entertainment", "total": 15.00, "percent": 2},
        {"name": "Food", "total": 12.50, "percent": 2},
    ]

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
