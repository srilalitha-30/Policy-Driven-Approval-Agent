import os
from typing import Optional


class Settings:
    """Application settings loaded from environment variables."""
    
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./approval_agent.db")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    debug: bool = os.getenv("DEBUG", "True").lower() == "true"


settings = Settings()
