# src/app/core/notifier.py

import httpx
import logging
from app.config.config import settings

logger = logging.getLogger(__name__)

async def send_telegram_notification(user_telegram_id: int, message: str):
    """
    Sends a message to a specific user via the Telegram Bot API.
    """
    bot_token = settings.TELEGRAM_BOT_TOKEN
    if not bot_token:
        logger.error("TELEGRAM_BOT_TOKEN not found. Cannot send notification.")
        return

    api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": user_telegram_id,
        "text": message,
        "parse_mode": "HTML", # Allows for bold, italics, and links
        "disable_web_page_preview": True,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(api_url, json=payload)
            response.raise_for_status() # Raise an exception for bad responses (4xx or 5xx)
            logger.info(f"Successfully sent notification to user {user_telegram_id}")
        except httpx.HTTPStatusError as e:
            logger.error(f"Error sending notification to {user_telegram_id}: {e.response.text}")
        except Exception as e:
            logger.error(f"An unexpected error occurred in notifier: {e}")