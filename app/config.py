# app/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Your app's API credentials.
    # It's best practice to load these from environment variables.
    API_ID: int
    API_HASH: str
    DEFAULT_SESSION_NAME: str = "default_session"

    # Directories
    SESSIONS_DIR: str = "sessions/"
    LOGS_DIR: str = "logs/"

    class Config:
        # This will automatically look for a .env file
        env_file = ".env"

settings = Settings()

# In a real app, this user data would come from a database.
# For now, we'll keep it here for simplicity.
USER_SETTINGS = {
    'Abel A': {
        'keywords': ['urgent', 'invoice', 'project alpha'],
        'notification_method': 'log',
    },
    'bini': {
        'keywords': ['meeting', 'deadline', 'project beta'],
        'notification_method': 'email',
    },
}