
# Loads all environment variables (API keys, database URLs, secrets, etc.) and provides them to the entire application from one place.
from typing import List, Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    APP_NAME: str = "AI Email Assistant"
    APP_ENV: str = "development"  # development | staging | production
    DEBUG: bool = True
    
    # DB & Redis
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_email_assistant"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Google OAuth
    GOOGLE_CLIENT_ID: str = "your_google_client_id.apps.googleusercontent.com"
    GOOGLE_CLIENT_SECRET: str = "your_google_client_secret"
    
    # OpenAI & ElevenLabs
    OPENAI_API_KEY: str = "sk-xxxxxxxxxxxxxxxxxxxxx"
    ELEVENLABS_API_KEY: str = "el_xxxxxxxxxxxxxxxxxxxxx"
    
    # Qdrant Vector DB
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = ""
    
    # Sentry DSN
    SENTRY_DSN: Optional[str] = None
    
    # LangChain / LangSmith
    LANGCHAIN_API_KEY: Optional[str] = None
    
    # JWT Secret
    SECRET_KEY: str = "change_this_to_a_long_random_string"
    
    # CORS
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000,https://app.yourdomain.com"
    
    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.APP_ENV in ("production", "staging"):
            # Variables required in production/staging and must not be default placeholders
            required_vars = {
                "DATABASE_URL": self.DATABASE_URL,
                "REDIS_URL": self.REDIS_URL,
                "GOOGLE_CLIENT_ID": self.GOOGLE_CLIENT_ID,
                "GOOGLE_CLIENT_SECRET": self.GOOGLE_CLIENT_SECRET,
                "OPENAI_API_KEY": self.OPENAI_API_KEY,
                "ELEVENLABS_API_KEY": self.ELEVENLABS_API_KEY,
                "QDRANT_URL": self.QDRANT_URL,
                "SECRET_KEY": self.SECRET_KEY,
                "SENTRY_DSN": self.SENTRY_DSN,
                "LANGCHAIN_API_KEY": self.LANGCHAIN_API_KEY,
            }
            
            placeholders = [
                "your_google_client_id",
                "your_google_client_secret",
                "sk-xxxxxxxxxxxxxxxxxxxxx",
                "el_xxxxxxxxxxxxxxxxxxxxx",
                "change_this_to_a_long_random_string",
                "xxxxxxxxxxxxxxxxxxxxx",
            ]
            
            missing = []
            for name, val in required_vars.items():
                if not val:
                    missing.append(name)
                elif any(ph in str(val) for ph in placeholders):
                    missing.append(name)
            
            if missing:
                raise ValueError(
                    f"Production/Staging mode enabled, but the following required environment "
                    f"variables are missing or use default placeholders: {', '.join(missing)}"
                )
        return self

settings = Settings()
