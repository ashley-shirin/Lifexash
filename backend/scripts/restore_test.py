"""Prove that a backup can be restored: load it into a throw-away database and compare row counts.

Run from backend/ (venv active):
    python -m scripts.restore_test                     # tests the newest backup
    python -m scripts.restore_test path\\to\\file.sql    # tests a specific backup

Safety: local MySQL only (see db_url() in backup_db.py). The real database is only READ (row counts).
The backup is restored into lifexash_restore_test, which is always dropped at the end.
Needs this grant once (as root):
    GRANT ALL PRIVILEGES ON `lifexash_restore_test`.* TO 'LifeXash'@'localhost';
"""

import re
import subprocess
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.core.database import engine
from scripts.backup_db import BACKUP_DIR, BACKUP_NAME, check_dump, db_url, find_mysql_tool, mysql_option_file

TEST_DB = "lifexash_restore_test"
ACCESS_DENIED = 1044  # MySQL error: no privileges on that database


def sql_for_test_db(dump: str, source_db: str) -> str:
    """Remove the dump's CREATE DATABASE / USE lines, so it can't write into the real database.

    A dump made with --databases contains "CREATE DATABASE `lifexash`" and "USE `lifexash`;". Without them,
    the SQL runs in whatever database mysql is started with (--database=lifexash_restore_test).
    """
    kept = []
    for line in dump.splitlines(keepends=True):
        if re.match(r"^\s*(CREATE DATABASE|USE)\b", line, re.IGNORECASE):
            continue
        kept.append(line)
    sql = "".join(kept)

    # Double check: no statement (comment lines aside) may still name the real database.
    # Case-insensitive: on Windows MySQL, `LifeXash` and `lifexash` are the same database.
    real_db = f"`{source_db}`".lower()
    for line in sql.splitlines():
        if not line.startswith("--") and real_db in line.lower():
            raise ValueError(f"the dump still refers to `{source_db}`: {line[:80]!r}")
    return sql


def row_counts(conn, database: str) -> dict[str, int]:
    tables = conn.execute(
        text("SELECT TABLE_NAME FROM information_schema.TABLES WHERE TABLE_SCHEMA = :db AND TABLE_TYPE = 'BASE TABLE'"),
        {"db": database},
    ).scalars()
    # Exact COUNT(*): information_schema.TABLE_ROWS is only an estimate for InnoDB.
    return {t: conn.execute(text(f"SELECT COUNT(*) FROM `{database}`.`{t}`")).scalar() for t in sorted(tables)}


def main() -> int:
    url = db_url()
    source_db = url.database
    if source_db.lower() == TEST_DB:
        sys.exit(f"ERROR: DATABASE_URL points at {TEST_DB}; refusing to run.")

    if len(sys.argv) > 1:
        backup = Path(sys.argv[1])
    else:
        backups = sorted(p for p in BACKUP_DIR.glob("*.sql") if BACKUP_NAME.match(p.name))
        if not backups:
            sys.exit(f"ERROR: no backups in {BACKUP_DIR}. Run: python -m scripts.backup_db")
        backup = backups[-1]

    check_dump(backup)
    print(f"Backup:  {backup}")
    sql = sql_for_test_db(backup.read_text(encoding="utf-8"), source_db)
    mysql = find_mysql_tool("mysql")

    try:
        with engine.connect() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS `{TEST_DB}`"))  # leftover from an interrupted run
            conn.execute(text(f"CREATE DATABASE `{TEST_DB}` CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"))
    except OperationalError as exc:
        if exc.orig.args[0] != ACCESS_DENIED:
            raise
        print(f"ERROR: {url.username} may not create {TEST_DB}. Run this once as root, then try again:")
        print(f"    GRANT ALL PRIVILEGES ON `{TEST_DB}`.* TO '{url.username}'@'{url.host or 'localhost'}';")
        return 1
    print(f"Created: {TEST_DB}")

    try:

        with mysql_option_file(url) as option_file:
            result = subprocess.run(
                [mysql, f"--defaults-extra-file={option_file}", "--default-character-set=utf8mb4", f"--database={TEST_DB}"],
                input=sql.encode("utf-8"),  # fed straight to mysql's stdin, no shell in between
                capture_output=True,
            )
        if result.returncode != 0:
            print(f"ERROR: restore failed (exit {result.returncode}):\n{result.stderr.decode(errors='replace').strip()}")
            return 1
        print(f"Restored into {TEST_DB}\n")

        with engine.connect() as conn:
            original = row_counts(conn, source_db)
            restored = row_counts(conn, TEST_DB)

        all_ok = original.keys() == restored.keys()
        print(f"{'table':<18}{source_db:>12}{'restored':>12}   result")
        for table in sorted(original.keys() | restored.keys()):
            a, b = original.get(table, "-"), restored.get(table, "-")
            ok = a == b
            all_ok &= ok
            print(f"{table:<18}{a!s:>12}{b!s:>12}   {'OK' if ok else 'DIFF'}")
        print()
        print("RESULT: backup restores correctly." if all_ok else
              "RESULT: DIFFERENCES found (did the app write data after the backup was made?)")
        return 0 if all_ok else 1
    finally:
        with engine.connect() as conn:
            conn.execute(text(f"DROP DATABASE IF EXISTS `{TEST_DB}`"))
        print(f"Dropped: {TEST_DB}")


if __name__ == "__main__":
    sys.exit(main())
