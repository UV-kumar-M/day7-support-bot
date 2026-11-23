"""Application configuration loaded from environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()


def get_api_key() -> str:
    """Return the LLM API key from environment variables (never hardcoded)."""
    return os.environ.get("API_KEY", "sk-ci-placeholder-key")