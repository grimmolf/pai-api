from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field
from functools import lru_cache

class Settings(BaseSettings):
    # System Identity
    SYSTEM_NAME: str = Field(default="Bob", description="Name of the local PAI identity")

    # Server Config
    PORT: int = Field(default=8000, description="Port to run the local API server on")
    API_KEY: SecretStr = Field(default=SecretStr("dev-key"), description="Local API Key for authentication")

    # Remote Config
    REMOTE_PAI_URL: str = Field(default="http://localhost:8000", description="Full URL of the remote PAI instance")
    REMOTE_PAI_API_KEY: SecretStr = Field(default=SecretStr("dev-key"), description="API Key for the remote PAI instance")

    # Database Config
    DB_PATH: str = Field(default="data/messages.db", description="Path to SQLite database file")

    model_config = SettingsConfigDict(
        env_prefix="PAI_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

@lru_cache()
def get_settings():
    return Settings()
