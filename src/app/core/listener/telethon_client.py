# app/core/telethon_client.py

import logging
import os
from telethon import TelegramClient
from app.config.config import settings

logger = logging.getLogger(__name__)
# A dictionary to hold all active client instances, keyed by session name.
# This will be managed by the startup/shutdown events in main.py
ACTIVE_CLIENTS = {}

def get_telethon_client(session_name: str) -> TelegramClient:
    """
    Creates and returns a Telethon client instance for a given session.
    """
    session_path = os.path.join(settings.SESSIONS_DIR, f"{session_name}")
    logger.info(f"Creating Telethon client for session: {session_name} at {session_path}")
    client = TelegramClient(
        session_path,
        settings.API_ID,
        settings.API_HASH
    )
    return client