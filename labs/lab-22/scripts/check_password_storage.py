import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.data.database import SessionLocal
from app.data.models import User


def main():
    db = SessionLocal()
    try:
        users = db.scalars(select(User).order_by(User.id)).all()
        for user in users:
            status = (
                "HASHED"
                if user.password_hash.startswith("$argon2")
                else "LEGACY"
            )
            print(f"{user.username}: {status}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
