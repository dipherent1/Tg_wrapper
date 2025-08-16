# create_session.py
import asyncio
import os
from telethon import TelegramClient
from app.config.config import settings # Make sure this path works from your root

SESSION_NAME = settings.DEFAULT_SESSION_NAME
API_ID = settings.API_ID
API_HASH = settings.API_HASH

# Use the absolute path from your settings to be safe
SESSION_DIR = settings.SESSIONS_DIR
SESSION_PATH = SESSION_DIR / SESSION_NAME

async def main():
    print(f"Authorizing session '{SESSION_NAME}'...")
    
    # This will create the client object
    client = TelegramClient(str(SESSION_PATH), API_ID, API_HASH)
    await client.start()
    
    me = await client.get_me()
    print(f"Success! Session for {me.first_name} (@{me.username}) has been created at: {SESSION_PATH}.session")
    
    await client.disconnect()

if __name__ == "__main__":
    # Ensure the sessions directory exists
    SESSION_DIR.mkdir(exist_ok=True)
    asyncio.run(main())