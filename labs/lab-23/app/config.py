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

    database_url: str = "sqlite:///./cloud_application.db"

    storage_path: str = "storage/objects"
    max_upload_size: int = 5 * 1024 * 1024

    https_enabled: bool = False
    https_port: int = 8443
    ssl_certfile: str | None = None
    ssl_keyfile: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
