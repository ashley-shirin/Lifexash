"""Check the database that DATABASE_URL points at (made for TiDB Cloud, also works on local MySQL).

Run from backend/ (venv active), after `alembic upgrade head`:
    python -m scripts.verify_remote_db

Checks: TLS is in use, all tables exist (right collation, migrations at head), whether the mood CHECK
constraint is enforced (only reported), that deleting a user CASCADE-deletes all their rows, and that
utf8mb4 stores emoji.

Safe for real data: it only writes rows that belong to its own test user (verify-remote-db-…@example.invalid),
and deletes that user again at the end, even if a check fails. Real users' rows are only counted, never changed.
Exit code 0 = all checks passed, 1 = at least one FAIL.
"""

import sys
import uuid
from datetime import date, time
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import delete, func, select, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal, connect_args_for, engine
from app.models import JournalEntry, Note, Tag, Task, User, note_tags

EXPECTED_TABLES = {"alembic_version", "users", "tasks", "notes", "tags", "note_tags", "journal_entries"}
EXPECTED_COLLATION = "utf8mb4_0900_ai_ci"
EMAIL_PREFIX = "verify-remote-db-"
EMAIL_DOMAIN = "@example.invalid"  # .invalid can never be a real domain
EMOJI_TEXT = "utf8mb4 check 😀🎉 ñ 日本"
CHECK_VIOLATION = 3819  # MySQL/TiDB error: check constraint violated

failures = 0


def report(status: str, label: str, detail: str = "") -> None:
    global failures
    if status == "FAIL":
        failures += 1
    print(f"[{status}] {label}" + (f": {detail}" if detail else ""))


def delete_test_user(db: Session, user_id: int) -> None:
    """Remove the test user's rows child-first, so clean-up also works if CASCADE is broken."""
    note_ids = select(Note.id).where(Note.user_id == user_id)
    db.execute(delete(note_tags).where(note_tags.c.note_id.in_(note_ids)))
    for model in (JournalEntry, Task, Note, Tag):
        db.execute(delete(model).where(model.user_id == user_id))
    db.execute(delete(User).where(User.id == user_id))
    db.commit()


def remove_leftovers(db: Session) -> None:
    """Delete test users left behind by an earlier run that crashed (only our own test emails)."""
    pattern = f"{EMAIL_PREFIX}%{EMAIL_DOMAIN}"
    for user_id in db.scalars(select(User.id).where(User.email.like(pattern))).all():
        delete_test_user(db, user_id)
        report("INFO", "Removed a test user left over from an earlier run", f"id {user_id}")


def check_tls() -> None:
    with engine.connect() as conn:
        version = conn.execute(text("SELECT VERSION()")).scalar()
        cipher = conn.execute(text("SHOW SESSION STATUS LIKE 'Ssl_cipher'")).one()[1]
    report("INFO", "Server version", version)
    if connect_args_for(settings.DATABASE_URL):  # remote host: TLS is required and the certificate verified
        if cipher:
            report("PASS", "TLS in use, certificate verified (certifi CA bundle)", cipher)
        else:
            report("FAIL", "TLS in use", "no cipher: the connection is NOT encrypted")
    else:
        report("INFO", "Local database: TLS is optional here, certificate not verified", cipher or "no TLS")


def check_tables() -> None:
    with engine.connect() as conn:
        rows = conn.execute(
            text("SELECT TABLE_NAME, TABLE_COLLATION FROM information_schema.TABLES WHERE TABLE_SCHEMA = DATABASE()")
        ).all()
        collations = {name: collation for name, collation in rows}
        missing = EXPECTED_TABLES - collations.keys()
        if missing:
            report("FAIL", "Tables exist", f"missing: {', '.join(sorted(missing))}. Run `alembic upgrade head`.")
            return
        report("PASS", "Tables exist", ", ".join(sorted(EXPECTED_TABLES)))

        wrong = {t: collations[t] for t in EXPECTED_TABLES - {"alembic_version"} if collations[t] != EXPECTED_COLLATION}
        if wrong:
            report("FAIL", f"Table collation {EXPECTED_COLLATION}", f"different: {wrong}")
        else:
            report("PASS", f"Table collation {EXPECTED_COLLATION}")

        current = conn.execute(text("SELECT version_num FROM alembic_version")).scalar()
    alembic_ini = Path(__file__).resolve().parents[1] / "alembic.ini"
    head = ScriptDirectory.from_config(Config(str(alembic_ini))).get_current_head()
    if current == head:
        report("PASS", "Migrations at head", current)
    else:
        report("FAIL", "Migrations at head", f"database is at {current}, code is at {head}")


def check_mood_constraint(user_id: int) -> None:
    with engine.connect() as conn:
        create_sql = conn.execute(text("SHOW CREATE TABLE journal_entries")).one()[1]
    defined = "ck_journal_entries_mood_range" in create_sql

    with SessionLocal() as db:
        db.add(JournalEntry(user_id=user_id, entry_date=date(2000, 1, 1), content="bad mood", mood=6))
        try:
            db.commit()
            enforced = False
        except DBAPIError as e:
            db.rollback()
            if e.orig.args[0] != CHECK_VIOLATION:
                raise
            enforced = True

    if enforced:
        report("INFO", "mood CHECK constraint (1-5)", "ENFORCED by the database (mood 6 rejected with error 3819)")
    else:
        detail = "NOT enforced: mood 6 was saved (the API's validation still rejects it with 422)"
        if not defined:
            detail += ". The constraint isn't in SHOW CREATE TABLE (TiDB drops it unless tidb_enable_check_constraint was ON)"
        report("INFO", "mood CHECK constraint (1-5)", detail)
        # The row is removed with the test user (cascade), or by delete_test_user().


def check_emoji_and_cascade(user_id: int) -> None:
    with SessionLocal() as db:
        tag = Tag(user_id=user_id, name="verify")
        note = Note(user_id=user_id, title="verify", content=EMOJI_TEXT, tags=[tag])
        db.add_all([
            note,
            Task(user_id=user_id, title="verify", task_date=date(2000, 1, 2), task_time=time(9, 0)),
            JournalEntry(user_id=user_id, entry_date=date(2000, 1, 2), content=EMOJI_TEXT, mood=4),
        ])
        db.commit()
        note_id, tag_id = note.id, tag.id

    # Read back in a NEW session, so the value really comes from the database, not from memory.
    with SessionLocal() as db:
        stored = db.scalar(select(Note.content).where(Note.id == note_id))
    if stored == EMOJI_TEXT:
        report("PASS", "utf8mb4: emoji saved and read back unchanged", stored)
    else:
        report("FAIL", "utf8mb4: emoji saved and read back unchanged", f"got {stored!r}")

    def counts(db: Session) -> dict[str, int]:
        return {
            "tasks": db.scalar(select(func.count()).where(Task.user_id == user_id)),
            "notes": db.scalar(select(func.count()).where(Note.user_id == user_id)),
            "tags": db.scalar(select(func.count()).where(Tag.user_id == user_id)),
            "note_tags": db.scalar(
                select(func.count()).select_from(note_tags)
                .where((note_tags.c.note_id == note_id) | (note_tags.c.tag_id == tag_id))
            ),
            "journal_entries": db.scalar(select(func.count()).where(JournalEntry.user_id == user_id)),
        }

    with SessionLocal() as db:
        before = counts(db)
        # Delete ONLY the users row. Everything else must be removed by the database (ON DELETE CASCADE).
        db.execute(delete(User).where(User.id == user_id))
        db.commit()
        after = counts(db)

    if all(before.values()) and not any(after.values()):
        report("PASS", "Deleting the user CASCADE-deleted all their rows", f"before {before}, after: all 0")
    else:
        report("FAIL", "Deleting the user CASCADE-deleted all their rows", f"before {before}, after {after}")


def main() -> int:
    # Windows may print with an old code page (cp1252) that has no emoji; UTF-8 can print them.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    url = engine.url
    print(f"Database: {url.database} on {url.host}:{url.port or 3306}\n")

    check_tls()
    check_tables()
    if failures:  # without the tables, the other checks can't run
        return 1

    with SessionLocal() as db:
        remove_leftovers(db)
        user = User(name="Verify script", email=f"{EMAIL_PREFIX}{uuid.uuid4().hex[:12]}{EMAIL_DOMAIN}", password_hash="x")
        db.add(user)
        db.commit()
        user_id = user.id

    try:
        check_mood_constraint(user_id)
        check_emoji_and_cascade(user_id)
    finally:
        # Always clean up. After a successful cascade there's nothing left, which is fine.
        with SessionLocal() as db:
            delete_test_user(db, user_id)
            left = db.scalar(select(func.count()).where(User.id == user_id))
        report("PASS" if left == 0 else "FAIL", "Test user removed", f"id {user_id}")

    # Name the target in the last line, so a copied "All checks passed" always says WHICH database it was.
    # (A local run was once reported as a TiDB run: DATABASE_URL wasn't set in that terminal.)
    kind = "REMOTE database (verified TLS)" if connect_args_for(settings.DATABASE_URL) else "LOCAL database, NOT the cloud one"
    result = "All checks passed" if failures == 0 else f"{failures} check(s) FAILED"
    print(f"\n{result} on {url.host}:{url.port or 3306}, {kind}.")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
