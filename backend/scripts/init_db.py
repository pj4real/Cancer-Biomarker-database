"""Create/upgrade the schema, import the curated sample dataset and compute evidence scores.

Usage (from backend/):
    python -m scripts.init_db                    # migrate + import data/sample + score
    python -m scripts.init_db --data path/to/dir # import a different curated directory
    python -m scripts.init_db --reset            # SQLite only: delete the DB file first
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402

from app.config import BACKEND_DIR, get_settings  # noqa: E402

DEFAULT_DATA = BACKEND_DIR / "data" / "sample"


def migrate() -> None:
    cfg = Config(str(BACKEND_DIR / "alembic.ini"))
    cfg.set_main_option("script_location", str(BACKEND_DIR / "alembic"))
    command.upgrade(cfg, "head")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    url = get_settings().resolved_database_url
    if args.reset:
        if not url.startswith("sqlite:///"):
            print("--reset is only supported for SQLite. Drop the PostgreSQL database manually.")
            return 2
        Path(url.removeprefix("sqlite:///")).unlink(missing_ok=True)

    print(f"Database: {url.split('@')[-1]}")
    migrate()
    print("Schema is at the latest migration.")

    # Imported after migration so the engine sees the created file.
    from app.database import SessionLocal
    from app.services.importer import import_directory
    from app.services.scores import recompute_all

    with SessionLocal() as db:
        reports = import_directory(db, args.data)
        for r in reports:
            status = "OK " if r.ok else "ERR"
            print(f"  [{status}] {r.entity:<20} rows={r.rows_total:<4} inserted={r.inserted:<4} "
                  f"updated={r.updated:<4} unchanged={r.unchanged}")
            for e in r.errors[:20]:
                print(f"        row {e['row']}: {e['field'] or ''} {e['message']}")
        if not all(r.ok for r in reports):
            print("Import stopped because of validation errors.")
            return 1
        n = recompute_all(db)
        print(f"Evidence-support scores computed for {n} associations.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
