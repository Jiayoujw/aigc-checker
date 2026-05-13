import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))


class Config:
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com/v1"
    DEEPSEEK_MODEL: str = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    DEFAULT_PROVIDER: str = os.getenv("DEFAULT_PROVIDER", "deepseek")

    SERPAPI_KEY: str = os.getenv("SERPAPI_KEY", "")

    MAX_TEXT_LENGTH: int = 50000
    MIN_TEXT_LENGTH: int = 50


config = Config()
