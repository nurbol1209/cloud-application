from pydantic_settings import BaseSettings, SettingsConfigDict


class NotificationSettings(BaseSettings):
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


settings = NotificationSettings()
