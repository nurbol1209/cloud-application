import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.data.database import SessionLocal
from app.data.models import User
from app.security.passwords import hash_password


def is_argon2_hash(value: str) -> bool:
    return value.startswith("$argon2")


def main():
    db = SessionLocal()
    converted = 0
    try:
        users = db.scalars(select(User)).all()
        for user in users:
            if is_argon2_hash(user.password_hash):
                continue
            user.password_hash = hash_password(user.password_hash)
            converted += 1
        db.commit()
        print(f"Passwords converted: {converted}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
