from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    API_KEY: str = "dev-key"  # Local API Key
    SYSTEM_NAME: str = "Bob"
    PORT: int = 8000
    
    # Remote Configuration
    REMOTE_PAI_URL: str = "http://localhost:8000" # Default to self for testing
    REMOTE_PAI_API_KEY: str = "dev-key"
    
    model_config = SettingsConfigDict(env_prefix="PAI_", env_file=".env")

@lru_cache()
def get_settings():
    return Settings()
