"""Application configuration settings."""
import os
from pathlib import Path
from dotenv import load_dotenv
import yaml

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE_DIR / "config" / "settings.yaml"


def load_yaml_config() -> dict:
    """Load configuration from settings.yaml."""
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            return yaml.safe_load(f) or {}
    return {}


class Settings:
    """Application settings."""
    
    def __init__(self):
        config = load_yaml_config()
        
        # Secrets from .env
        self.OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
        
        # Server config from settings.yaml
        server = config.get("server", {})
        self.HOST: str = server.get("host", "0.0.0.0")
        self.PORT: int = server.get("port", 8000)
        self.DEBUG: bool = server.get("debug", True)
        
        # Database config from settings.yaml
        database = config.get("database", {})
        self.DATABASE_PATH: Path = BASE_DIR / database.get("path", "data/receptionist.db")
        
        # OpenAI config from settings.yaml
        openai_config = config.get("openai", {})
        self.OPENAI_MODEL: str = openai_config.get("model", "gpt-4o-mini")
        
        # CORS config from settings.yaml
        cors = config.get("cors", {})
        self.CORS_ORIGINS: list[str] = cors.get("origins", ["*"])


settings = Settings()
