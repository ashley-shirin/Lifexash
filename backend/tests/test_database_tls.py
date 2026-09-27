"""TLS to the database: required + verified for every remote host (e.g. TiDB Cloud), PyMySQL's default
for a local MySQL. No database needed.

Also checks that the backup scripts refuse to run against a remote database.
"""

import ssl

import pytest

from app.core.database import connect_args_for
from scripts import backup_db

# Placeholders in the TiDB Cloud format, not a real cluster.
TIDB_URL = "mysql+pymysql://PREFIX.lifexash_app:pw@gateway01.REGION.prod.aws.tidbcloud.com:4000/lifexash?charset=utf8mb4"


@pytest.mark.parametrize(
    "url",
    [
        "mysql+pymysql://user:pw@localhost:3306/lifexash?charset=utf8mb4",
        "mysql+pymysql://user:pw@127.0.0.1:3306/lifexash",
        "mysql+pymysql://user:pw@[::1]:3306/lifexash",
    ],
)
def test_local_database_gets_no_tls_settings(url):
    assert connect_args_for(url) == {}


def test_remote_database_gets_verified_tls():
    ctx = connect_args_for(TIDB_URL)["ssl"]
    assert isinstance(ctx, ssl.SSLContext)
    assert ctx.verify_mode == ssl.CERT_REQUIRED  # the certificate must be signed by a trusted CA...
    assert ctx.check_hostname is True  # ...and issued for the host we connect to
    assert ctx.cert_store_stats()["x509_ca"] > 0  # certifi's CA bundle was loaded


def test_backup_scripts_refuse_a_remote_database(monkeypatch):
    monkeypatch.setattr(backup_db.settings, "DATABASE_URL", TIDB_URL)
    with pytest.raises(SystemExit, match="local MySQL only"):
        backup_db.db_url()


def test_backup_scripts_accept_a_local_database(monkeypatch):
    monkeypatch.setattr(backup_db.settings, "DATABASE_URL", "mysql+pymysql://user:pw@localhost:3306/lifexash")
    assert backup_db.db_url().database == "lifexash"
