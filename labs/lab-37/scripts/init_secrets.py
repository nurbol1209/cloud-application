import secrets
from pathlib import Path

SECRETS_DIR = Path(__file__).resolve().parent.parent / "secrets"


def write_secret(path: Path, value: str) -> None:
    if path.exists() and path.read_text(encoding="utf-8").strip():
        print(f"{path.name}: already configured")
        return
    path.write_text(value, encoding="utf-8")
    print(f"{path.name}: generated")


def main() -> None:
    SECRETS_DIR.mkdir(exist_ok=True)
    write_secret(SECRETS_DIR / "lab_db_password", "cloud_application")
    write_secret(
        SECRETS_DIR / "auth_secret",
        secrets.token_urlsafe(32),
    )


if __name__ == "__main__":
    main()
