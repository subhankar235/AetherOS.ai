
# Loads all environment variables (API keys, database URLs, secrets, etc.) and provides them to the entire application from one place.
from typing import List, Optional
from pydantic import model_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True
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
    GOOGLE_REDIRECT_URI: str = Field("http://localhost:8000/integrations/google/callback", alias="GOOGLE_REDIRECT_URI")
    GOOGLE_PUBSUB_VERIFICATION_TOKEN: str = Field("change_this_webhook_verification_token", alias="GOOGLE_PUBSUB_VERIFICATION_TOKEN")
    token_encryption_key: str = Field("change_this_to_a_32_byte_key", alias="TOKEN_ENCRYPTION_KEY")
    RATE_LIMIT_GMAIL_PER_MIN: int = Field(60, alias="RATE_LIMIT_GMAIL_PER_MIN")
    RATE_LIMIT_CALENDAR_PER_MIN: int = Field(60, alias="RATE_LIMIT_CALENDAR_PER_MIN")
    CELERY_BROKER_URL: str = Field("redis://localhost:6379/1", alias="CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND: str = Field("redis://localhost:6379/2", alias="CELERY_RESULT_BACKEND")
    
    # OpenAI & ElevenLabs
    OPENAI_API_KEY: str = "sk-xxxxxxxxxxxxxxxxxxxxx"
    ELEVENLABS_API_KEY: str = "sk_17c9803ed2daa90d1f648c98d93d21c5be8ffb63074beebb"
    ELEVENLABS_VOICE_ID: str = "OtEfb2LVzIE45wdYe54M"
    ELEVENLABS_STT_MODEL: str = "eleven-stt-v1"
    ELEVENLABS_TTS_MODEL: str = "eleven-multilingual-v2"
    ELEVENLABS_DEFAULT_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"
    ELEVENLABS_DEFAULT_MODEL_ID: str = "eleven_flash_v2_5"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-large"
    
    # Qdrant Vector DB
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: Optional[str] = ""
    QDRANT_COLLECTION_COMPANY_MEMORY: str = "company_memory"
    QDRANT_COLLECTION_RESEARCH_CACHE: str = "research_cache"
    QDRANT_COLLECTION_SUPPORT_KB: str = "support_kb"
    
    # Sentry DSN
    # Web Search
    TAVILY_API_KEY: Optional[str] = None
    
    SENTRY_DSN: Optional[str] = None
    
    # LangChain / LangSmith
    LANGCHAIN_API_KEY: Optional[str] = None
    
    # JWT Secret
    SECRET_KEY: str = "change_this_to_a_long_random_string"
    
    # CORS
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000,https://app.yourdomain.com"
    
    # --- Clerk (identity/session — see Phase 5) ---
    clerk_secret_key: str = Field(..., alias="CLERK_SECRET_KEY")
    clerk_publishable_key: str = Field(..., alias="CLERK_PUBLISHABLE_KEY")
    clerk_webhook_signing_secret: str = Field(..., alias="CLERK_WEBHOOK_SIGNING_SECRET")
    CLERK_JWT_ISSUER: Optional[str] = Field(None, alias="CLERK_JWT_ISSUER")
    clerk_jwks_url: Optional[str] = Field(None, alias="CLERK_JWKS_URL")
    clerk_issuer: Optional[str] = Field(None, alias="CLERK_ISSUER")  # e.g. https://your-app-name.clerk.accounts.dev

    # Feature flags
    PAYMENT_AGENT_ENABLED: bool = False
    
    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]

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

settings = Settings()  # type: ignore[call-arg]
