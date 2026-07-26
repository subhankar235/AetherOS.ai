
# Loads all environment variables (API keys, database URLs, secrets, etc.) and provides them to the entire application from one place.
from typing import Optional
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True
    )

    APP_NAME: str = "AI Email Assistant"
    APP_ENV: str = "development"
    DEBUG: bool = True

    DATABASE_URL: Optional[str] = None
    REDIS_URL: Optional[str] = None
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None
    FRONTEND_BASE_URL: Optional[str] = None
    GOOGLE_PUBSUB_VERIFICATION_TOKEN: Optional[str] = None
    TOKEN_ENCRYPTION_KEY: Optional[str] = None
    RATE_LIMIT_GMAIL_PER_MIN: int = 60
    RATE_LIMIT_CALENDAR_PER_MIN: int = 60

    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: Optional[str] = None
    OPENAI_MODEL_PRIMARY: Optional[str] = None
    OPENAI_MODEL_CLASSIFIER: Optional[str] = None

    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: Optional[str] = None
    LLM_FALLBACK_ORDER: Optional[str] = None

    ELEVENLABS_API_KEY: Optional[str] = None
    ELEVENLABS_VOICE_ID: Optional[str] = None
    ELEVENLABS_STT_MODEL: Optional[str] = None
    ELEVENLABS_TTS_MODEL: Optional[str] = None
    ELEVENLABS_DEFAULT_VOICE_ID: Optional[str] = None
    ELEVENLABS_DEFAULT_MODEL_ID: Optional[str] = None
    OPENAI_EMBEDDING_MODEL: Optional[str] = None

    QDRANT_URL: Optional[str] = None
    QDRANT_API_KEY: Optional[str] = None
    QDRANT_COLLECTION_RESEARCH_CACHE: Optional[str] = None

    TAVILY_API_KEY: Optional[str] = None
    BRAVE_SEARCH_API_KEY: Optional[str] = None
    SERPER_API_KEY: Optional[str] = None
    FIRECRAWL_API_KEY: Optional[str] = None
    SENTRY_DSN: Optional[str] = None
    LANGCHAIN_API_KEY: Optional[str] = None
    SECRET_KEY: Optional[str] = None
    CORS_ALLOWED_ORIGINS: Optional[str] = None

    CLERK_SECRET_KEY: Optional[str] = None
    CLERK_PUBLISHABLE_KEY: Optional[str] = None
    CLERK_WEBHOOK_SIGNING_SECRET: Optional[str] = None
    CLERK_JWT_ISSUER: Optional[str] = None

    clerk_issuer: Optional[str] = None
    clerk_jwks_url: Optional[str] = None

    @model_validator(mode="after")
    def set_clerk_defaults(self) -> "Settings":
        if not self.clerk_issuer and self.CLERK_JWT_ISSUER:
            issuer = self.CLERK_JWT_ISSUER
            if not issuer.startswith("http"):
                issuer = f"https://{issuer}"
            self.clerk_issuer = issuer
        if not self.clerk_jwks_url and self.clerk_issuer:
            self.clerk_jwks_url = f"{self.clerk_issuer.rstrip('/')}/.well-known/jwks.json"
        return self

settings = Settings()
