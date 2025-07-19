# src/app/core/event_handler.py

import logging
import asyncio
from telethon import events, TelegramClient

# Import our new worker function
from .worker import process_new_message

logger = logging.getLogger(__name__)

def setup_event_handlers(client: TelegramClient):
    """
    Attaches a simple event handler that triggers our worker function
    for every new incoming message.
    """
    
    @client.on(events.NewMessage(incoming=True))
    async def new_message_trigger(event: events.NewMessage.Event):
        """
        This function's only job is to 'trigger' the real processing logic.
        We run it as a background task to prevent blocking the event loop.
        """
        logger.info(f"New message received in chat {event.chat_id}: {event.raw_text}")
        
        # This is a "fire-and-forget" approach. The listener can immediately
        # go back to listening for the next message while this one is processed.
        # asyncio.create_task(process_new_message(event))

    logger.info("✅ Event handler trigger for new messages has been set up.")