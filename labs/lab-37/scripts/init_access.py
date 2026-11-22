import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.data.database import SessionLocal
from app.services.access import (
    assign_default_roles,
    initialize_access_model,
)


def main():
    db = SessionLocal()
    try:
        initialize_access_model(db)
        assign_default_roles(db)
        print("Access model initialized")
    finally:
        db.close()


if __name__ == "__main__":
    main()
