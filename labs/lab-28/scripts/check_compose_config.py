"""Проверка compose.yaml без запуска Docker.

Скрипт разбирает YAML и проверяет контракты лабораторной работы:
сервисы, сеть, volume, secrets, healthcheck, порядок запуска и
отсутствие пароля БД в самом compose-файле.
"""

import sys
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).resolve().parent.parent
COMPOSE_PATH = BASE_DIR / "compose.yaml"
INIT_SQL = BASE_DIR / "docker" / "postgres" / "01_base_schema.sql"
SECRET_FILES = [
    BASE_DIR / "secrets" / "lab_db_password",
    BASE_DIR / "secrets" / "auth_secret",
]

failures: list[str] = []
warnings: list[str] = []


def check(condition: bool, message: str) -> None:
    print(f"[{'OK' if condition else 'FAIL'}] {message}")
    if not condition:
        failures.append(message)


def warn(condition: bool, message: str) -> None:
    print(f"[{'OK' if condition else 'WARN'}] {message}")
    if not condition:
        warnings.append(message)


def main() -> int:
    text = COMPOSE_PATH.read_text(encoding="utf-8")
    config = yaml.safe_load(text)

    print("== Сервисы ==")
    services = config.get("services", {})
    check(set(services) == {"app", "db", "migrate"}, "сервисы app, db, migrate")

    db = services.get("db", {})
    app = services.get("app", {})
    migrate = services.get("migrate", {})

    check(db.get("image") == "postgres:18", "db использует postgres:18")
    db_env = db.get("environment", {})
    check(db_env.get("POSTGRES_DB") == "cloud_application", "POSTGRES_DB")
    check(db_env.get("POSTGRES_USER") == "postgres", "POSTGRES_USER")
    check(
        db_env.get("POSTGRES_PASSWORD_FILE") == "/run/secrets/lab_db_password",
        "пароль БД читается из файла секрета",
    )
    check("POSTGRES_PASSWORD" not in db_env, "пароль не задан открыто")
    check("ports" not in db, "PostgreSQL не опубликован на host port")

    db_volumes = db.get("volumes", [])
    check(
        any(item.startswith("postgres_data:") for item in db_volumes),
        "postgres_data подключён к db",
    )
    check(
        any("docker-entrypoint-initdb.d" in item and item.endswith(":ro")
            for item in db_volumes),
        "init SQL смонтирован только для чтения",
    )

    healthcheck = db.get("healthcheck", {})
    check(
        "pg_isready" in str(healthcheck.get("test", "")),
        "healthcheck использует pg_isready",
    )

    print("\n== Порядок запуска ==")
    migrate_depends = migrate.get("depends_on", {})
    check(
        migrate_depends.get("db", {}).get("condition") == "service_healthy",
        "migrate ждёт healthy db",
    )
    app_depends = app.get("depends_on", {})
    check(
        app_depends.get("migrate", {}).get("condition")
        == "service_completed_successfully",
        "app ждёт успешного завершения migrate",
    )

    print("\n== Конфигурация приложения ==")
    for name, service in (("app", app), ("migrate", migrate)):
        env = service.get("environment", {})
        check(env.get("DB_HOST") == "db", f"{name}: DB_HOST=db")
        check(
            env.get("DB_BACKEND") == "postgresql",
            f"{name}: DB_BACKEND=postgresql",
        )
    check(
        "127.0.0.1:8080:8000" in app.get("ports", []),
        "app публикуется как 127.0.0.1:8080:8000",
    )

    print("\n== Сеть, volume, secrets ==")
    check("postgres_data" in config.get("volumes", {}), "volume postgres_data")
    check(
        "cloud-network" in config.get("networks", {}),
        "сеть cloud-network",
    )
    for name, service in (("db", db), ("app", app), ("migrate", migrate)):
        check(
            "cloud-network" in service.get("networks", []),
            f"{name} подключён к cloud-network",
        )

    secret_defs = config.get("secrets", {})
    check(
        set(secret_defs) == {"lab_db_password", "auth_secret"},
        "секреты lab_db_password и auth_secret определены",
    )
    for name, definition in secret_defs.items():
        path = definition.get("file", "")
        check(path.startswith("./secrets/"), f"{name}: файл в secrets/")

    app_secret_targets = {
        item.get("target") for item in app.get("secrets", []) if isinstance(item, dict)
    }
    check(
        app_secret_targets == {
            "/app/secrets/lab_db_password",
            "/app/secrets/auth_secret",
        },
        "app получает оба секрета в /app/secrets",
    )

    print("\n== Файлы секретов ==")
    for path in SECRET_FILES:
        exists = path.is_file()
        warn(exists, f"{path.name} существует локально")
        if exists and path.stat().st_size > 0:
            value = path.read_text(encoding="utf-8").strip()
            password_lines = [
                line
                for line in text.splitlines()
                if "PASSWORD" in line.upper() and not line.strip().startswith("#")
            ]
            check(
                all(value not in line for line in password_lines),
                f"значение {path.name} не попало в строки с паролем",
            )

    print("\n== Init SQL ==")
    check(INIT_SQL.is_file(), "01_base_schema.sql существует")
    if INIT_SQL.is_file():
        sql = INIT_SQL.read_text(encoding="utf-8")
        for fragment in (
            "CREATE TABLE service_types",
            "CREATE TABLE services",
            "INSERT INTO service_types",
            "INSERT INTO services",
        ):
            check(fragment in sql, f"init SQL содержит {fragment}")

    print("\n== Итог ==")
    if warnings:
        for message in warnings:
            print(f"WARN: {message}")
    if failures:
        for message in failures:
            print(f"FAIL: {message}")
        return 1
    print("PASS: compose.yaml соответствует требованиям лабораторной работы")
    return 0


if __name__ == "__main__":
    sys.exit(main())
