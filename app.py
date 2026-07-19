import os
from datetime import date, datetime

from flask import Flask, abort, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database.db import (
    CATEGORIES,
    create_expense,
    create_user,
    delete_expense as db_delete_expense,
    get_category_breakdown,
    get_db,
    get_expense_by_id,
    get_expense_stats,
    get_expenses_by_user,
    get_user_by_email,
    get_user_by_id,
    init_db,
    seed_db,
    update_expense,
)

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


def _parse_date_arg(value):
    if not value:
        return None
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None
    return value


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    start_date = _parse_date_arg(request.args.get("start"))
    end_date = _parse_date_arg(request.args.get("end"))
    if start_date and end_date and start_date > end_date:
        start_date, end_date = None, None

    user = get_user_by_id(session["user_id"])
    stats = get_expense_stats(session["user_id"], start_date, end_date)
    transactions = get_expenses_by_user(session["user_id"], start_date, end_date)
    categories = get_category_breakdown(session["user_id"], start_date, end_date)

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
        start_date=start_date,
        end_date=end_date,
    )


@app.route("/expenses/add", methods=["GET", "POST"])
def add_expense():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    today = date.today().isoformat()

    if request.method == "POST":
        amount_raw = request.form.get("amount", "")
        category = request.form.get("category", "")
        expense_date = request.form.get("date", "")
        description = request.form.get("description", "").strip() or None

        error = None
        try:
            amount = float(amount_raw)
            if amount <= 0:
                error = "Amount must be greater than 0."
        except ValueError:
            amount = None
            error = "Amount must be a valid number."

        if not error and category not in CATEGORIES:
            error = "Please select a valid category."

        if not error:
            try:
                datetime.strptime(expense_date, "%Y-%m-%d")
            except ValueError:
                error = "Please enter a valid date."

        if error:
            return render_template(
                "add_expense.html",
                error=error,
                categories=CATEGORIES,
                today=today,
                amount=amount_raw,
                category=category,
                date=expense_date,
                description=description or "",
            )

        create_expense(session["user_id"], amount, category, expense_date, description)
        return redirect(url_for("profile"))

    return render_template("add_expense.html", categories=CATEGORIES, today=today)


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
def edit_expense(id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    expense = get_expense_by_id(id, session["user_id"])
    if expense is None:
        abort(404)

    if request.method == "POST":
        amount_raw = request.form.get("amount", "")
        category = request.form.get("category", "")
        expense_date = request.form.get("date", "")
        description = request.form.get("description", "").strip() or None

        error = None
        try:
            amount = float(amount_raw)
            if amount <= 0:
                error = "Amount must be greater than 0."
        except ValueError:
            amount = None
            error = "Amount must be a valid number."

        if not error and category not in CATEGORIES:
            error = "Please select a valid category."

        if not error:
            try:
                datetime.strptime(expense_date, "%Y-%m-%d")
            except ValueError:
                error = "Please enter a valid date."

        if error:
            return render_template(
                "edit_expense.html",
                error=error,
                categories=CATEGORIES,
                expense={
                    "id": id,
                    "amount": amount_raw,
                    "category": category,
                    "date": expense_date,
                    "description": description or "",
                },
            )

        update_expense(id, session["user_id"], amount, category, expense_date, description)
        return redirect(url_for("profile"))

    return render_template("edit_expense.html", expense=expense, categories=CATEGORIES)


@app.route("/expenses/<int:id>/delete", methods=["POST"])
def delete_expense(id):
    if not session.get("user_id"):
        return redirect(url_for("login"))

    expense = get_expense_by_id(id, session["user_id"])
    if expense is None:
        abort(404)

    db_delete_expense(id, session["user_id"])
    return redirect(url_for("profile"))


if __name__ == "__main__":
    app.run(debug=True, port=5001)
