import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings


def configured(value) -> str:
    return (
        "CONFIGURED"
        if value.get_secret_value()
        else "EMPTY"
    )


def main() -> None:
    print("LAB_DB_PASSWORD:", configured(settings.lab_db_password))
    print("AUTH_SECRET:", configured(settings.auth_secret))

    auth_secret = settings.auth_secret.get_secret_value()
    if len(auth_secret) < 32:
        print("AUTH_SECRET: TOO SHORT")
    else:
        print("AUTH_SECRET: LENGTH OK")

    if settings.ssl_keyfile:
        key_path = Path(settings.ssl_keyfile)
        print(
            "TLS_PRIVATE_KEY:",
            "EXISTS" if key_path.exists() else "MISSING",
        )
    else:
        print("TLS_PRIVATE_KEY: NOT CONFIGURED")


if __name__ == "__main__":
    main()
