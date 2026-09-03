import os
import sqlite3
import click
from flask import current_app, g, has_app_context
from werkzeug.security import generate_password_hash

# Path to SQLite database file
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "spendly.db")


def get_db(db_path=None):
    """
    Returns a SQLite connection with row_factory and foreign keys enabled.
    Supports both Flask application context (caching in flask.g) and standalone script execution.
    """
    if has_app_context():
        target_path = db_path or current_app.config.get("DATABASE", DB_PATH)
        if "db" not in g:
            conn = sqlite3.connect(target_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            g.db = conn
        return g.db
    else:
        target_path = db_path or DB_PATH
        conn = sqlite3.connect(target_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn


def close_db(e=None):
    """
    Closes the database connection if open in flask.g.
    Can be registered with app.teardown_appcontext.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(conn=None):
    """
    Creates all tables using CREATE TABLE IF NOT EXISTS.
    """
    db = conn or get_db()
    with db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                icon TEXT DEFAULT '🏷️',
                color TEXT DEFAULT '#4F46E5'
            );

            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                category_id INTEGER,
                title TEXT NOT NULL,
                amount REAL NOT NULL,
                date DATE NOT NULL,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS subscriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan_id TEXT NOT NULL,
                amount REAL NOT NULL,
                payment_method TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            );
        """)
    return db


def seed_db(conn=None):
    """
    Inserts initial categories, a demo user, and sample expenses for development.
    """
    db = conn or get_db()
    cursor = db.cursor()

    # 1. Seed Categories
    categories = [
        ("Food & Dining", "🍔", "#F59E0B"),
        ("Groceries", "🛒", "#10B981"),
        ("Transportation", "🚗", "#3B82F6"),
        ("Shopping", "🛍️", "#EC4899"),
        ("Housing & Rent", "🏠", "#8B5CF6"),
        ("Bills & Utilities", "💡", "#EAB308"),
        ("Entertainment", "🎬", "#6366F1"),
        ("Healthcare", "🏥", "#EF4444"),
        ("Education", "📚", "#14B8A6"),
        ("Miscellaneous", "📦", "#6B7280"),
    ]
    cursor.executemany(
        """
        INSERT OR IGNORE INTO categories (name, icon, color)
        VALUES (?, ?, ?)
        """,
        categories,
    )

    # 2. Seed Demo User
    demo_password_hash = generate_password_hash("password123")
    cursor.execute(
        """
        INSERT OR IGNORE INTO users (name, email, password_hash)
        VALUES (?, ?, ?)
        """,
        ("Nitish Kumar", "nitish@example.com", demo_password_hash),
    )

    # 3. Seed Sample Expenses for demo user
    cursor.execute("SELECT id FROM users WHERE email = ?", ("nitish@example.com",))
    user_row = cursor.fetchone()

    if user_row:
        user_id = user_row["id"]

        # Retrieve category IDs map
        cursor.execute("SELECT id, name FROM categories")
        cat_map = {row["name"]: row["id"] for row in cursor.fetchall()}

        sample_expenses = [
            (user_id, cat_map.get("Food & Dining"), "Dinner with friends", 1250.00, "2026-08-28", "Italian Bistro"),
            (user_id, cat_map.get("Groceries"), "Weekly Grocery Run", 2400.50, "2026-08-29", "Supermarket"),
            (user_id, cat_map.get("Transportation"), "Cab ride to office", 350.00, "2026-08-30", "Uber"),
            (user_id, cat_map.get("Bills & Utilities"), "Electricity Bill", 1800.00, "2026-08-31", "August bill"),
            (user_id, cat_map.get("Entertainment"), "Movie tickets", 600.00, "2026-09-01", "PVR Cinemas"),
        ]

        cursor.execute("SELECT COUNT(*) as count FROM expenses WHERE user_id = ?", (user_id,))
        if cursor.fetchone()["count"] == 0:
            cursor.executemany(
                """
                INSERT INTO expenses (user_id, category_id, title, amount, date, notes)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                sample_expenses,
            )

    db.commit()
    return db


@click.command("init-db")
def init_db_command():
    """Clear existing data and create new tables."""
    init_db()
    click.echo("Initialized the database.")


@click.command("seed-db")
def seed_db_command():
    """Seed default categories, demo user, and sample expenses."""
    init_db()
    seed_db()
    click.echo("Seeded the database.")


def init_app(app):
    """
    Registers database functions and CLI commands with the Flask application.
    """
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(seed_db_command)


if __name__ == "__main__":
    print(f"Initializing database at: {DB_PATH}")
    init_db()
    print("Database initialized.")
    print("Seeding database with default categories and demo user...")
    seed_db()
    print("Database seeded successfully!")

