"""Settings validation: the app must refuse to start with a missing or weak JWT_SECRET.

_env_file=None: ignore backend/.env, so each test only sees the values it passes in.
"""

import pytest
from pydantic import ValidationError

from app.core.config import Settings

DB_URL = "mysql+pymysql://user:pw@localhost:3306/test"
GOOD_SECRET = "x" * 32


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    # Real environment variables would win over the values below, so remove them for these tests.
    for name in ("DATABASE_URL", "JWT_SECRET", "JWT_EXPIRE_MINUTES", "CORS_ORIGINS"):
        monkeypatch.delenv(name, raising=False)


def test_missing_jwt_secret_is_rejected():
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(_env_file=None, DATABASE_URL=DB_URL)


def test_short_jwt_secret_is_rejected():
    with pytest.raises(ValidationError, match="at least 32 characters"):
        Settings(_env_file=None, DATABASE_URL=DB_URL, JWT_SECRET="x" * 31)


def test_missing_database_url_is_rejected():
    with pytest.raises(ValidationError, match="DATABASE_URL"):
        Settings(_env_file=None, JWT_SECRET=GOOD_SECRET)


def test_valid_settings_and_defaults():
    settings = Settings(_env_file=None, DATABASE_URL=DB_URL, JWT_SECRET=GOOD_SECRET)
    assert settings.JWT_EXPIRE_MINUTES == 60
    assert settings.CORS_ORIGINS == ["http://localhost:5173"]


def test_cors_origins_from_comma_separated_env(monkeypatch):
    monkeypatch.setenv("CORS_ORIGINS", "https://lifexash.app, https://www.lifexash.app/ ,")
    settings = Settings(_env_file=None, DATABASE_URL=DB_URL, JWT_SECRET=GOOD_SECRET)
    assert settings.CORS_ORIGINS == ["https://lifexash.app", "https://www.lifexash.app"]
