import os
import functools
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import init_app, get_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-spendly-2026")
init_app(app)


def login_required(view):
    """Decorator to require login for protected views."""
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if session.get("user_id") is None:
            return redirect(url_for("login"))
        return view(**kwargs)
    return wrapped_view


@app.template_filter("date_format")
def format_date(date_str):
    """Formats timestamp or date string to 'Month Day, Year'."""
    if not date_str:
        return ""
    try:
        clean_date = str(date_str).split()[0]
        dt = datetime.strptime(clean_date, "%Y-%m-%d")
        return dt.strftime("%B %d, %Y")
    except Exception:
        return str(date_str)


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        error = None

        if not name:
            error = "Full name is required."
        elif not email or "@" not in email:
            error = "A valid email address is required."
        elif not password:
            error = "Password is required."
        elif len(password) < 8:
            error = "Password must be at least 8 characters long."
        else:
            db = get_db()
            existing_user = db.execute(
                "SELECT id FROM users WHERE email = ?", (email,)
            ).fetchone()

            if existing_user is not None:
                error = "An account with this email already exists."
            else:
                password_hash = generate_password_hash(password)
                db.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    (name, email, password_hash),
                )
                db.commit()
                return redirect(url_for("login"))

        return render_template("register.html", error=error, name=name, email=email)

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        error = None

        if not email or not password:
            error = "Email and password are required."
        else:
            db = get_db()
            user = db.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()

            if user is None or not check_password_hash(user["password_hash"], password):
                error = "Invalid email or password."
            else:
                session.clear()
                session["user_id"] = user["id"]
                session["user_name"] = user["name"]
                return redirect(url_for("profile"))

        return render_template("login.html", error=error, email=email)

    if session.get("user_id"):
        return redirect(url_for("profile"))

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
    return redirect(url_for("login"))


@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user_id = session["user_id"]
    db = get_db()
    profile_error = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()

        if not name:
            profile_error = "Full name is required."
        elif not email or "@" not in email:
            profile_error = "A valid email address is required."
        else:
            existing_user = db.execute(
                "SELECT id FROM users WHERE email = ? AND id != ?", (email, user_id)
            ).fetchone()

            if existing_user is not None:
                profile_error = "An account with this email already exists."
            else:
                db.execute(
                    "UPDATE users SET name = ?, email = ? WHERE id = ?",
                    (name, email, user_id),
                )
                db.commit()
                session["user_name"] = name
                flash("Profile updated successfully.", "profile_success")
                return redirect(url_for("profile"))

    user = db.execute(
        "SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,)
    ).fetchone()

    stats = db.execute(
        "SELECT COUNT(*) AS total_count, COALESCE(SUM(amount), 0.0) AS total_amount FROM expenses WHERE user_id = ?",
        (user_id,),
    ).fetchone()

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        profile_error=profile_error,
    )


@app.route("/profile/password", methods=["POST"])
@login_required
def change_password():
    user_id = session["user_id"]
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")

    db = get_db()
    user = db.execute(
        "SELECT password_hash FROM users WHERE id = ?", (user_id,)
    ).fetchone()

    if not current_password or not new_password or not confirm_password:
        flash("All password fields are required.", "password_error")
    elif not check_password_hash(user["password_hash"], current_password):
        flash("Current password is incorrect.", "password_error")
    elif len(new_password) < 8:
        flash("New password must be at least 8 characters long.", "password_error")
    elif new_password != confirm_password:
        flash("New passwords do not match.", "password_error")
    else:
        new_hash = generate_password_hash(new_password)
        db.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (new_hash, user_id),
        )
        db.commit()
        flash("Password updated successfully.", "password_success")

    return redirect(url_for("profile"))


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
