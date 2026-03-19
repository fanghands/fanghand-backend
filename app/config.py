from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # App
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000"]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fanghand"
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""
    JWT_SECRET: str = "dev-jwt-secret"
    JWT_ALGORITHM: str = "HS256"

    # Stripe
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_COLLECTOR: str = ""
    STRIPE_PRICE_RESEARCHER: str = ""
    STRIPE_PRICE_LEAD: str = ""
    STRIPE_PRICE_PREDICTOR: str = ""
    STRIPE_PRICE_TWITTER: str = ""
    STRIPE_PRICE_CLIP: str = ""
    STRIPE_PRICE_BROWSER: str = ""
    STRIPE_PRICE_BUNDLE_ANALYST: str = ""
    STRIPE_PRICE_BUNDLE_GROWTH: str = ""
    STRIPE_PRICE_BUNDLE_CREATOR: str = ""
    STRIPE_PRICE_BUNDLE_FULLSTACK: str = ""

    # Solana
    SOLANA_RPC_URL: str = "https://api.mainnet-beta.solana.com"
    PLATFORM_WALLET_PUBKEY: str = "PLT1111111111111111111111111111111111111111"
    PLATFORM_BURN_KEYPAIR: str = ""
    FGH_TOKEN_MINT: str = "29W2v9vodbzFQWjshgq1u119VW8MvVgsksrLhZ5ipump"
    USDC_TOKEN_MINT: str = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    QUICK_RUN_LAMPORTS: int = 8_000_000
    DEEP_RUN_LAMPORTS: int = 25_000_000
    CREDIT_DEPOSIT_MIN: int = 10_000_000

    # OpenFang
    OPENFANG_API_URL: str = "http://localhost:4200"
    OPENFANG_API_KEY: str = ""

    # Redis
    REDIS_URL: str = "redis://localhost:6379"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # Email (Resend)
    RESEND_API_KEY: str = ""
    FROM_EMAIL: str = "no-reply@fanghand.xyz"

    # Sentry
    SENTRY_DSN: str = ""

    model_config = {"env_file": ".env", "case_sensitive": True}

    @property
    def async_database_url(self) -> str:
        """Convert Railway's postgres:// to postgresql+asyncpg://"""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif not url.startswith("postgresql+asyncpg://"):
            url = "postgresql+asyncpg://" + url.split("://", 1)[-1]
        return url


settings = Settings()
