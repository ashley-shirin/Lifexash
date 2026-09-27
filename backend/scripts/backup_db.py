"""Back up the LifeXash database with mysqldump.

Run from backend/ (venv active):
    python -m scripts.backup_db

- Connection details come from DATABASE_URL (backend/.env or the environment).
- Saves to %USERPROFILE%\\Documents\\LifeXash-backups\\lifexash_YYYY-MM-DD_HHMM.sql — outside the project,
  so a backup can never be committed. (A plain local folder: not synced to OneDrive.)
- The password never goes on the command line and is never printed: mysqldump reads it from a temporary
  option file that only exists while the dump runs.
- Keeps the 10 newest backups and deletes older ones.
- LOCAL MySQL only: it refuses to run when DATABASE_URL points at another host (e.g. TiDB Cloud). The
  mysqldump options are MySQL-specific and connect without TLS; use TiDB Cloud's own backups there.

To check that a backup really restores, run:  python -m scripts.restore_test
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import datetime
from glob import glob
from pathlib import Path

from sqlalchemy.engine import URL, make_url

from app.core.config import settings
from app.core.database import LOCAL_HOSTS

BACKUP_DIR = Path(os.environ["USERPROFILE"]) / "Documents" / "LifeXash-backups"
BACKUP_NAME = re.compile(r"^lifexash_\d{4}-\d{2}-\d{2}_\d{4}\.sql$")  # only these files are ever deleted
KEEP = 10


def find_mysql_tool(name: str) -> str:
    """Full path of mysqldump / mysql: on PATH first, else the newest C:\\Program Files\\MySQL\\MySQL Server *."""
    on_path = shutil.which(name)
    if on_path:
        return on_path
    installed = sorted(glob(rf"C:\Program Files\MySQL\MySQL Server *\bin\{name}.exe"))
    if installed:
        return installed[-1]
    sys.exit(f"ERROR: {name} not found on PATH or in C:\\Program Files\\MySQL\\. Install MySQL Server or add its bin folder to PATH.")


def db_url() -> URL:
    """DATABASE_URL, split into parts. Stops the script unless it points at a database on this machine."""
    # make_url splits the URL into parts and decodes %-escaped characters in the password.
    url = make_url(settings.DATABASE_URL)
    if url.host not in LOCAL_HOSTS:
        # Also protects restore_test.py (it uses this function): it must never create databases in the cloud.
        sys.exit(f"ERROR: DATABASE_URL points at {url.host}, not a local MySQL. These scripts are for local MySQL only.")
    return url


def _option_value(value: str) -> str:
    # Option-file values in double quotes: escape \ and " so any password works.
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


@contextmanager
def mysql_option_file(url: URL) -> Iterator[str]:
    """A temporary [client] option file with the login details; always deleted afterwards.

    Pass it as the FIRST argument: --defaults-extra-file=<path>. This keeps the password out of the
    command line (visible to other programs) and out of the environment (MYSQL_PWD is deprecated).
    """
    fd, path = tempfile.mkstemp(prefix="lifexash_", suffix=".cnf")  # in your user temp folder
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write("[client]\n")
            f.write(f"user={_option_value(url.username or '')}\n")
            f.write(f"password={_option_value(url.password or '')}\n")
            f.write(f"host={url.host or 'localhost'}\n")
            f.write(f"port={url.port or 3306}\n")
        yield path
    finally:
        os.remove(path)


def check_dump(path: Path) -> None:
    """Raise ValueError unless the file looks like a complete mysqldump file."""
    size = path.stat().st_size
    if size == 0:
        raise ValueError("backup file is empty")
    with path.open("rb") as f:
        if not f.read(13).startswith(b"-- MySQL dump"):
            raise ValueError('backup file does not start with "-- MySQL dump"')
        f.seek(max(0, size - 200))
        # mysqldump writes this last line only if it finished: catches a dump that stopped halfway.
        if b"-- Dump completed" not in f.read():
            raise ValueError('backup file does not end with "-- Dump completed" (incomplete dump?)')


def remove_old_backups() -> list[Path]:
    backups = sorted(p for p in BACKUP_DIR.iterdir() if BACKUP_NAME.match(p.name))  # names sort by date
    old = backups[:-KEEP]
    for path in old:
        path.unlink()
    return old


def main() -> int:
    url = db_url()
    mysqldump = find_mysql_tool("mysqldump")
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    target = BACKUP_DIR / f"lifexash_{datetime.now():%Y-%m-%d_%H%M}.sql"
    if target.exists():
        print(f"ERROR: {target.name} already exists (one backup per minute). Try again in a minute.")
        return 1

    print(f"mysqldump: {mysqldump}")
    print(f"Database:  {url.database} on {url.host or 'localhost'}:{url.port or 3306} as {url.username}")

    with mysql_option_file(url) as option_file:
        result = subprocess.run(
            [
                mysqldump,
                f"--defaults-extra-file={option_file}",  # must be the first option
                "--databases", url.database,
                "--no-tablespaces",  # no PROCESS privilege needed; we don't use tablespaces
                "--single-transaction",  # consistent snapshot of InnoDB tables without locking them
                # GTID is ON on this server. Without this, mysqldump runs FLUSH TABLES (needs the RELOAD
                # privilege) to record the GTID position — only useful for replication, which we don't use.
                "--set-gtid-purged=OFF",
                "--default-character-set=utf8mb4",  # keep emoji and accents intact
                f"--result-file={target}",  # mysqldump writes the file itself: no PowerShell ">" encoding issues
            ],
            capture_output=True,
            text=True,
        )

    if result.returncode != 0:
        print(f"ERROR: mysqldump failed (exit {result.returncode}):\n{result.stderr.strip()}")
        target.unlink(missing_ok=True)
        return 1
    try:
        check_dump(target)
    except ValueError as exc:
        print(f"ERROR: {exc}. Deleted {target.name}.")
        target.unlink()
        return 1

    print(f"Backup OK: {target}")
    print(f"Size:      {target.stat().st_size / 1024:.1f} KB")
    for path in remove_old_backups():
        print(f"Removed old backup: {path.name}")
    kept = sum(1 for p in BACKUP_DIR.iterdir() if BACKUP_NAME.match(p.name))
    print(f"Backups kept: {kept} (max {KEEP})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
