import pytest

from app import create_app


@pytest.fixture
def app(tmp_path):
    return create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "test.sqlite"),
            "SECRET_KEY": "test-secret",
            "API_KEY": "test-key",
        }
    )


@pytest.fixture
def client(app):
    return app.test_client()
