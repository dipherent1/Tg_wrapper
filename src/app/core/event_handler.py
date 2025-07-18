# src/app/core/event_handler.py

import logging
from telethon import events, TelegramClient
from telethon.tl.types import User, Channel, Chat

# Get a logger for this module
logger = logging.getLogger(__name__)

async def new_message_handler(event: events.NewMessage.Event):
    """
    This function will be called for every new message in every chat
    the client is in.
    """
    try:
        # Get the chat entity to know its name and type
        chat = event.chat
        
        # Determine the chat type and name
        chat_title = ""
        if isinstance(chat, User):
            chat_title = chat.first_name
        elif isinstance(chat, (Channel, Chat)):
            chat_title = chat.title

        # Log the message cleanly
        logger.info(f"📬 New Message in '{chat_title}': '{event.raw_text[:80]}...'")
        
        # TODO: Here is where we will add the logic to:
        # 1. Save the message to the database.
        # 2. Check it against user subscriptions.
        # 3. Send notifications.

    except Exception as e:
        logger.error(f"Error in new_message_handler: {e}", exc_info=True)


def setup_event_handlers(client: TelegramClient):
    """Attaches all the event handlers to the client instance."""
    
    # Remove the `pass` and directly add the event handler function
    client.add_event_handler(new_message_handler, events.NewMessage(incoming=True))
    
    logger.info("✅ Event handler for new messages has been set up.")