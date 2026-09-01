import sqlite3
import pytest
from werkzeug.security import check_password_hash
from database.db import get_db, init_db, seed_db, close_db


def test_get_close_db(app):
    with app.app_context():
        db1 = get_db()
        db2 = get_db()
        assert db1 is db2

    # Verify that database connection is closed after app context tears down
    with pytest.raises(sqlite3.ProgrammingError, match="Cannot operate on a closed database"):
        db1.execute("SELECT 1")


def test_foreign_keys_enabled(app):
    with app.app_context():
        db = get_db()
        result = db.execute("PRAGMA foreign_keys;").fetchone()[0]
        assert result == 1


def test_row_factory_dict_access(app):
    with app.app_context():
        db = get_db()
        db.execute("INSERT INTO categories (name, icon, color) VALUES ('TestCat', '🧪', '#123456');")
        row = db.execute("SELECT name, icon, color FROM categories WHERE name = 'TestCat';").fetchone()
        assert row["name"] == "TestCat"
        assert row["icon"] == "🧪"
        assert row["color"] == "#123456"


def test_standalone_get_db(tmp_path):
    db_file = str(tmp_path / "standalone.db")
    db = get_db(db_file)
    init_db(db)
    result = db.execute("PRAGMA foreign_keys;").fetchone()[0]
    assert result == 1
    tables = [row["name"] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()]
    assert "users" in tables
    assert "categories" in tables
    assert "expenses" in tables
    db.close()


def test_init_db_creates_tables(app):
    with app.app_context():
        db = get_db()
        cursor = db.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row["name"] for row in cursor.fetchall()]
        assert "users" in tables
        assert "categories" in tables
        assert "expenses" in tables


def test_seed_db(app):
    with app.app_context():
        seed_db()
        db = get_db()

        # Verify categories seeded
        cat_count = db.execute("SELECT COUNT(*) as count FROM categories;").fetchone()["count"]
        assert cat_count == 10

        # Verify demo user seeded
        user = db.execute("SELECT * FROM users WHERE email = 'nitish@example.com';").fetchone()
        assert user is not None
        assert user["name"] == "Nitish Kumar"
        assert check_password_hash(user["password_hash"], "password123")

        # Verify sample expenses seeded
        expenses = db.execute("SELECT * FROM expenses WHERE user_id = ?;", (user["id"],)).fetchall()
        assert len(expenses) == 5


def test_seed_db_idempotency(app):
    with app.app_context():
        # Running seed_db multiple times should not cause duplicates or errors
        seed_db()
        seed_db()
        db = get_db()

        user_count = db.execute("SELECT COUNT(*) as count FROM users WHERE email = 'nitish@example.com';").fetchone()["count"]
        assert user_count == 1

        cat_count = db.execute("SELECT COUNT(*) as count FROM categories;").fetchone()["count"]
        assert cat_count == 10

        expense_count = db.execute("SELECT COUNT(*) as count FROM expenses;").fetchone()["count"]
        assert expense_count == 5


def test_foreign_key_cascade_user_delete(app):
    with app.app_context():
        seed_db()
        db = get_db()

        user = db.execute("SELECT id FROM users WHERE email = 'nitish@example.com';").fetchone()
        assert user is not None

        # Deleting user should cascade delete expenses
        db.execute("DELETE FROM users WHERE id = ?;", (user["id"],))
        db.commit()

        remaining_expenses = db.execute("SELECT COUNT(*) as count FROM expenses WHERE user_id = ?;", (user["id"],)).fetchone()["count"]
        assert remaining_expenses == 0


def test_foreign_key_set_null_category_delete(app):
    with app.app_context():
        seed_db()
        db = get_db()

        # Find category ID for Food & Dining
        cat = db.execute("SELECT id FROM categories WHERE name = 'Food & Dining';").fetchone()
        assert cat is not None

        # Expense before category deletion
        expense = db.execute("SELECT id, category_id FROM expenses WHERE category_id = ?;", (cat["id"],)).fetchone()
        assert expense is not None
        assert expense["category_id"] == cat["id"]

        # Delete the category
        db.execute("DELETE FROM categories WHERE id = ?;", (cat["id"],))
        db.commit()

        # Check expense category_id became NULL
        updated_expense = db.execute("SELECT id, category_id FROM expenses WHERE id = ?;", (expense["id"],)).fetchone()
        assert updated_expense["category_id"] is None


def test_cli_commands(runner):
    result_init = runner.invoke(args=["init-db"])
    assert result_init.exit_code == 0
    assert "Initialized the database." in result_init.output

    result_seed = runner.invoke(args=["seed-db"])
    assert result_seed.exit_code == 0
    assert "Seeded the database." in result_seed.output
