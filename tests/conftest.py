import pytest
from app import app as flask_app
from database.db import init_db


@pytest.fixture
def app(tmp_path):
    db_path = str(tmp_path / "test_spendly.db")

    flask_app.config.update({
        "TESTING": True,
        "DATABASE": db_path,
    })

    with flask_app.app_context():
        init_db()

    yield flask_app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()
