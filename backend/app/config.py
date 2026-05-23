from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    # SQLite by default (no Docker/Postgres required on Windows)
    DATABASE_URL: str = "sqlite+aiosqlite:///wardrobe.db"

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # File Storage
    UPLOAD_DIR: str = "./uploads"

    # AI Provider: mock (default), ollama, openai
    AI_PROVIDER: str = "mock"

    # AI Endpoints (comma-separated for fallback)
    AI_ENDPOINTS: str = "http://localhost:11434"

    # AI Models
    AI_VISION_MODEL: str = "llava"
    AI_TEXT_MODEL: str = "llama3"

    # AI Settings
    AI_TIMEOUT: int = 60
    AI_MAX_RETRIES: int = 3

    # API Keys (optional)
    AI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def parsed_ai_endpoints(self) -> List[str]:
        return [e.strip() for e in self.AI_ENDPOINTS.split(",") if e.strip()]

    @property
    def parsed_cors_origins(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()
