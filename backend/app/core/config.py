from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str | None = None
    SUPABASE_SECRET_KEY: str | None = None # Alias for SERVICE_ROLE_KEY
    
    @property
    def service_role_key(self) -> str:
        return self.SUPABASE_SERVICE_ROLE_KEY or self.SUPABASE_SECRET_KEY or ""
    GOOGLE_API_KEY: str
    GROQ_API_KEY: str | None = None
    OPENAI_API_KEY: str | None = None
    
    class Config:
        env_file = ["../.env", ".env"]
        extra = "ignore"

@lru_cache()
def get_settings():
    return Settings()
