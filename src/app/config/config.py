# app/config.py

import logging
from pydantic_settings import BaseSettings
from pathlib import Path
import json

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent #tg_wrapper/
class Settings(BaseSettings):
    # Your app's API credentials.
    # It's best practice to load these from environment variables.
    API_ID: int
    API_HASH: str
    DEFAULT_SESSION_NAME: str = "default_session"
    TELEGRAM_BOT_TOKEN: str = ""  
    DB_URL: str = ""
    # Directories
    SENTRY_DSN: str = ""
    SESSIONS_DIR: Path = BASE_DIR / "sessions"

    # TAGS_FILE_PATH: Path = BASE_DIR / "src/app/config/tags.json"
    LOGS_DIR: Path = BASE_DIR / "logs"
    class Config:
        # This will automatically look for a .env file
        env_file = ".env"

settings = Settings()

def setup_logging_directory():
    """Ensure that the necessary directories exist."""
    logger.info(f"Setting up logging directory at {settings.LOGS_DIR}, base dir: {BASE_DIR}")
    settings.LOGS_DIR.mkdir(parents=True, exist_ok=True)

def setup_sessions_directory():
    """Ensure that the sessions directory exists."""
    logger.info(f"Setting up sessions directory at {settings.SESSIONS_DIR}, base dir: {BASE_DIR}")
    settings.SESSIONS_DIR.mkdir(parents=True, exist_ok=True)

# def load_tags_from_config() -> list[dict]:
#     """Loads and validates the tags from the JSON configuration file."""
#     logger.info(f"Loading tags from {settings.TAGS_FILE_PATH}")
#     try:
#         with open(settings.TAGS_FILE_PATH, 'r') as f:
#             data = json.load(f)
        
#         # Basic validation
#         if "tags" in data and isinstance(data["tags"], list):
#             return data["tags"]
#         else:
#             # Handle error case where JSON is malformed
#             return []
#     except (FileNotFoundError, json.JSONDecodeError):
#         # Handle cases where the file doesn't exist or is invalid JSON
#         return []




# USER_SETTINGS = {
#     # 'Abel A': {
#     #     'keywords': ['urgent', 'invoice', 'project alpha'],
#     #     'notification_method': 'log',
#     # },
#     'bini': {
#         'keywords': ['meeting', 'deadline', 'project beta'],
#         'notification_method': 'email',
#     },
# }