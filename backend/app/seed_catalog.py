from __future__ import annotations

from backend.app.catalog_repository import seed_catalog_from_file
from backend.app.db import SessionLocal


def main() -> None:
    db = SessionLocal()
    try:
        count = seed_catalog_from_file(db)
        print(f"Seeded catalog tracks: {count}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
