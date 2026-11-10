import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select

from app.data.database import Base, SessionLocal, engine
from app.data.models import Service, ServiceType


INITIAL_TYPES = [
    ("application", "Application service"),
    ("database", "Database service"),
    ("monitoring", "Monitoring service"),
]

INITIAL_SERVICES = [
    ("Web Service", "application", "running"),
    ("Database Service", "database", "running"),
    ("Monitoring Service", "monitoring", "maintenance"),
]


def main():
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.scalar(select(ServiceType)) is None:
            for name, description in INITIAL_TYPES:
                db.add(ServiceType(name=name, description=description))
            db.commit()

        if db.scalar(select(Service)) is None:
            types = {
                item.name: item
                for item in db.scalars(select(ServiceType)).all()
            }
            for name, type_name, status in INITIAL_SERVICES:
                db.add(
                    Service(
                        name=name,
                        type_id=types[type_name].id,
                        status=status,
                    )
                )
            db.commit()

        print("Database initialized")
    finally:
        db.close()


if __name__ == "__main__":
    main()
