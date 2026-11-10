from urllib.parse import quote_plus

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Cloud Application"
    app_version: str = "1.0"
    app_description: str = (
        "Учебное облачное приложение для управления сервисами. "
        "Проект развивается в лабораторных работах по дисциплине "
        "«Управление работами и разработка программного обеспечения "
        "облачных систем»."
    )
    app_env: str = "development"
    app_host: str = "127.0.0.1"
    app_port: int = 8000
    debug: bool = True
    api_prefix: str = "/api"

    # "sqlite" — локальный учебный режим, "postgresql" — целевая СУБД.
    db_backend: str = "sqlite"
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "cloud_application"
    db_user: str = "postgres"

    lab_db_password: SecretStr
    auth_secret: SecretStr

    notification_service_url: str = "http://127.0.0.1:9000"
    notification_timeout_seconds: float = 2.0
    notification_max_attempts: int = 3
    notification_retry_delay_seconds: float = 0.5

    storage_path: str = "storage/objects"
    max_upload_size: int = 5 * 1024 * 1024

    https_enabled: bool = False
    https_port: int = 8443
    ssl_certfile: str | None = None
    ssl_keyfile: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        secrets_dir="secrets",
        case_sensitive=False,
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        if self.db_backend == "sqlite":
            return "sqlite:///./cloud_application.db"

        password = quote_plus(
            self.lab_db_password.get_secret_value()
        )
        return (
            "postgresql+psycopg2://"
            f"{self.db_user}:"
            f"{password}@"
            f"{self.db_host}:"
            f"{self.db_port}/"
            f"{self.db_name}"
        )


settings = Settings()
