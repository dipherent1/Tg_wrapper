# app/config.py

from pydantic_settings import BaseSettings
from pathlib import Path
import json


BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    # Your app's API credentials.
    # It's best practice to load these from environment variables.
    API_ID: int
    API_HASH: str
    DEFAULT_SESSION_NAME: str = "default_session"
    TELEGRAM_BOT_TOKEN: str = ""  
    DB_URL: str = ""
    # Directories
    SESSIONS_DIR: str = "sessions/"
    TAGS_FILE_PATH: Path = BASE_DIR / "config/tags.json"

    LOGS_DIR: str = "logs/"

    class Config:
        # This will automatically look for a .env file
        env_file = ".env"

settings = Settings()

# In a real app, this user data would come from a database.
# For now, we'll keep it here for simplicity.
def load_tags_from_config() -> list[dict]:
    """Loads and validates the tags from the JSON configuration file."""
    try:
        with open(settings.TAGS_FILE_PATH, 'r') as f:
            data = json.load(f)
        
        # Basic validation
        if "tags" in data and isinstance(data["tags"], list):
            return data["tags"]
        else:
            # Handle error case where JSON is malformed
            return []
    except (FileNotFoundError, json.JSONDecodeError):
        # Handle cases where the file doesn't exist or is invalid JSON
        return []




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