from pathlib import Path
from pydantic_settings import BaseSettings

_ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str = "http://localhost:8000/auth/callback"
    frontend_url: str = "http://localhost:3000"
    database_url: str = f"sqlite:///{Path(__file__).parent.parent.parent / 'exam.db'}"
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    gemini_api_key: str = ""
    groq_api_key: str = ""

    class Config:
        env_file = str(_ENV_FILE)


settings = Settings()
