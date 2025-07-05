# app/core/event_handler.py

import re
from telethon import events

def send_notification(user_config: dict, message_details: str):
    """Sends a notification based on the user's config."""
    print(f"  [!] NOTIFICATION: {message_details}")
    # Here you'd implement actual notification logic (email, webhook, etc.)

def setup_event_handlers(client: "TelegramClient", user_config: dict):
    """Attaches event handlers to a client instance."""
    
    @client.on(events.NewMessage(incoming=True))
    async def new_message_handler(event):
        message_text = event.raw_text
        for keyword in user_config.get('keywords', []):
            if re.search(keyword, message_text, re.IGNORECASE):
                # We found a match, send a notification
                send_notification(user_config, f"Keyword '{keyword}' found in message.")
                break # No need to check other keywords