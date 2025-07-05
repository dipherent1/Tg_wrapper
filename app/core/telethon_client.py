# app/core/telethon_client.py

import os
from telethon import TelegramClient
from ..config import settings

# A dictionary to hold all active client instances, keyed by session name.
# This will be managed by the startup/shutdown events in main.py
ACTIVE_CLIENTS = {}

# def get_default_client() -> TelegramClient:
#     """
#     Creates and returns a Telethon client instance for a given session.
#     """
#     session_path = os.path.join(settings.SESSIONS_DIR, f"{settings.DEFAULT_SESSION_NAME}.session")
#     client = TelegramClient(
#         session_path,
#         settings.API_ID,
#         settings.API_HASH
#     )
#     return client

def get_telethon_client(session_name: str) -> TelegramClient:
    """
    Creates and returns a Telethon client instance for a given session.
    """
    session_path = os.path.join(settings.SESSIONS_DIR, f"{session_name}.session")
    client = TelegramClient(
        session_path,
        settings.API_ID,
        settings.API_HASH
    )
    return client