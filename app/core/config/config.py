from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Setting(BaseSettings):
    """Application settings."""

    app_name: str = "FastAPI Application"
    debug: bool = Field(default=True, validation_alias="APP_DEBUG")
    database_url: str = Field(validation_alias="DATABASE_URL")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


# BaseSettings loads required values from the environment at runtime.
settings = Setting()  # pyright: ignore[reportCallIssue]