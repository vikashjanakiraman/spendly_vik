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


PLANS = {
    "monthly": {
        "id": "monthly",
        "name": "Spendly Pro (Monthly)",
        "price": 199.00,
        "period": "month",
        "badge": "Flexible",
        "features": [
            "Unlimited expense tracking",
            "Custom categories & tags",
            "Advanced monthly analytics & trends",
            "Export reports to CSV & Excel",
            "Priority customer support",
        ],
    },
    "annual": {
        "id": "annual",
        "name": "Spendly Pro (Annual)",
        "price": 1499.00,
        "period": "year",
        "badge": "Best Value (Save ~37%)",
        "features": [
            "Everything in Pro Monthly",
            "2 months free included",
            "Export PDF financial summaries",
            "Receipt attachments & photo capture",
            "Early access to upcoming features",
        ],
    },
}


@app.route("/pricing")
def pricing():
    user_id = session.get("user_id")
    active_sub = None
    if user_id:
        db = get_db()
        active_sub = db.execute(
            "SELECT * FROM subscriptions WHERE user_id = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1",
            (user_id,),
        ).fetchone()
    return render_template("pricing.html", plans=PLANS, active_sub=active_sub)


@app.route("/checkout/<plan_id>", methods=["GET", "POST"])
@login_required
def checkout(plan_id):
    if plan_id not in PLANS:
        return redirect(url_for("pricing"))

    plan = PLANS[plan_id]
    user_id = session["user_id"]
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    error = None

    if request.method == "POST":
        payment_method = request.form.get("payment_method", "card")
        card_name = request.form.get("card_name", "").strip()
        card_number = request.form.get("card_number", "").strip().replace(" ", "")
        card_exp = request.form.get("card_exp", "").strip()
        card_cvv = request.form.get("card_cvv", "").strip()
        upi_id = request.form.get("upi_id", "").strip()

        if payment_method == "card":
            if not card_name:
                error = "Name on card is required."
            elif not card_number or len(card_number) < 13 or not card_number.isdigit():
                error = "Please enter a valid card number (13-19 digits)."
            elif not card_exp or "/" not in card_exp or len(card_exp) != 5:
                error = "Please enter expiration date in MM/YY format."
            elif not card_cvv or len(card_cvv) < 3 or not card_cvv.isdigit():
                error = "Please enter a valid 3 or 4 digit CVV."
        elif payment_method == "upi":
            if not upi_id or "@" not in upi_id or len(upi_id) < 5:
                error = "Please enter a valid UPI ID (e.g. user@okhdfcbank)."
        else:
            error = "Invalid payment method selected."

        if not error:
            pay_detail = (
                f"Card ending in {card_number[-4:]}"
                if payment_method == "card"
                else f"UPI ({upi_id})"
            )
            cursor = db.execute(
                """
                INSERT INTO subscriptions (user_id, plan_id, amount, payment_method, status)
                VALUES (?, ?, ?, ?, 'active')
                """,
                (user_id, plan["id"], plan["price"], pay_detail),
            )
            db.commit()
            session["last_payment_id"] = cursor.lastrowid
            flash("Subscription activated successfully!", "payment_success")
            return redirect(url_for("payment_success"))

        return render_template(
            "checkout.html",
            plan=plan,
            user=user,
            error=error,
            payment_method=payment_method,
            card_name=card_name,
            card_number=card_number,
            card_exp=card_exp,
            upi_id=upi_id,
        )

    return render_template("checkout.html", plan=plan, user=user)


@app.route("/payment/success")
@login_required
def payment_success():
    user_id = session["user_id"]
    db = get_db()
    last_payment_id = session.get("last_payment_id")

    if last_payment_id:
        sub = db.execute(
            "SELECT * FROM subscriptions WHERE id = ? AND user_id = ?",
            (last_payment_id, user_id),
        ).fetchone()
    else:
        sub = db.execute(
            "SELECT * FROM subscriptions WHERE user_id = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1",
            (user_id,),
        ).fetchone()

    if not sub:
        return redirect(url_for("pricing"))

    plan = PLANS.get(
        sub["plan_id"],
        {"name": "Spendly Pro", "price": sub["amount"], "period": "cycle"},
    )

    return render_template("payment_success.html", subscription=sub, plan=plan)


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
    active_tab = request.args.get("tab", "overview")

    if request.method == "POST":
        active_tab = "settings"
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
                return redirect(url_for("profile", tab="settings"))

    user = db.execute(
        "SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,)
    ).fetchone()

    stats = db.execute(
        """
        SELECT 
            COUNT(*) AS total_count,
            COALESCE(SUM(amount), 0.0) AS total_amount,
            COALESCE(AVG(amount), 0.0) AS avg_amount,
            COALESCE(MAX(amount), 0.0) AS max_amount
        FROM expenses 
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()

    top_category = db.execute(
        """
        SELECT c.name, c.icon, c.color, SUM(e.amount) AS total
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = ?
        GROUP BY c.id
        ORDER BY total DESC
        LIMIT 1
        """,
        (user_id,),
    ).fetchone()

    categories_breakdown_raw = db.execute(
        """
        SELECT c.id, c.name, c.icon, c.color, COUNT(e.id) AS count, SUM(e.amount) AS total
        FROM expenses e
        JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = ?
        GROUP BY c.id
        ORDER BY total DESC
        """,
        (user_id,),
    ).fetchall()

    total_spent = stats["total_amount"] if stats and stats["total_amount"] else 0.0
    category_breakdown = []
    for cat in categories_breakdown_raw:
        pct = (cat["total"] / total_spent * 100) if total_spent > 0 else 0
        category_breakdown.append({
            "name": cat["name"],
            "icon": cat["icon"],
            "color": cat["color"],
            "count": cat["count"],
            "total": cat["total"],
            "percentage": round(pct, 1),
        })

    recent_expenses = db.execute(
        """
        SELECT e.id, e.title, e.amount, e.date, e.notes, 
               c.name AS category_name, c.icon AS category_icon, c.color AS category_color
        FROM expenses e
        LEFT JOIN categories c ON e.category_id = c.id
        WHERE e.user_id = ?
        ORDER BY e.date DESC, e.id DESC
        LIMIT 50
        """,
        (user_id,),
    ).fetchall()

    subscription = db.execute(
        "SELECT * FROM subscriptions WHERE user_id = ? AND status = 'active' ORDER BY created_at DESC LIMIT 1",
        (user_id,),
    ).fetchone()

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        top_category=top_category,
        category_breakdown=category_breakdown,
        recent_expenses=recent_expenses,
        subscription=subscription,
        profile_error=profile_error,
        active_tab=active_tab,
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

    return redirect(url_for("profile", tab="settings"))


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
