import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.data.database import engine

BASE_DIR = Path(__file__).resolve().parent.parent


def alembic_config() -> Config:
    config = Config(str(BASE_DIR / "alembic.ini"))
    config.set_main_option(
        "script_location",
        str(BASE_DIR / "migrations"),
    )
    return config


def create_sqlite_baseline() -> None:
    sql_file = BASE_DIR / "scripts" / "schema_baseline.sql"
    script = sql_file.read_text(encoding="utf-8")

    with engine.begin() as connection:
        for statement in script.split(";"):
            statement = statement.strip()
            if not statement:
                continue
            lines = [
                line
                for line in statement.splitlines()
                if not line.strip().startswith("--")
            ]
            prepared = "\n".join(lines).strip()
            if prepared:
                connection.exec_driver_sql(prepared)


def main():
    config = alembic_config()

    if engine.dialect.name != "sqlite":
        print(
            "PostgreSQL: выполните docs/sql/01_initial_schema.sql и "
            "docs/sql/02_initial_data.sql, затем alembic stamp 0001 "
            "и alembic upgrade head."
        )
        return

    inspector = inspect(engine)
    if "service_types" not in inspector.get_table_names():
        create_sqlite_baseline()
        print("SQLite baseline schema created")

    if "alembic_version" not in inspect(engine).get_table_names():
        command.stamp(config, "0001")
        print("Stamped baseline revision 0001")

    command.upgrade(config, "head")
    print("Database upgraded to head")


if __name__ == "__main__":
    main()
