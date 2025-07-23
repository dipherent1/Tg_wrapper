# src/app/core/worker.py

import logging
from telethon import events
from telethon.tl.types import Channel as TelethonChannel, Chat as TelethonChat

from app.domain import schemas

from app.services.message_service import save_new_message
from app.services.matching_service import run_matching_for_message
from app.domain.models import ChatType

logger = logging.getLogger(__name__)

async def process_new_message(event: events.NewMessage.Event):
    """
    The orchestrator function. It extracts all necessary data and
    calls the appropriate services.
    """
    try:
        logger.info(f"Processing new message in chat {event.chat_id}: {event.raw_text}")
        if not event.raw_text:
            return

        # --- THIS IS THE FIX ---
        # Step 1: Extract all available information from the event object.
        chat = await event.get_chat()
        
        # We are only interested in channels and supergroups for now.
        if not isinstance(chat, (TelethonChannel, TelethonChat)):
             return
        
        # --- NEW LOGIC: Determine the chat type ---
        chat_type = None
        if isinstance(chat, TelethonChannel):
            if chat.megagroup:
                chat_type = ChatType.SUPERGROUP
            else:
                chat_type = ChatType.CHANNEL
        elif isinstance(chat, TelethonChat):
            chat_type = ChatType.BASIC_GROUP

        channel_name = getattr(chat, 'title', None)
        channel_username = getattr(chat, 'username', None)

        channel_data = schemas.ChannelCreate(
            telegram_id=event.chat_id,
            name=channel_name,
            username=channel_username,
            type=chat_type # <-- Pass the type to the schema
        )

        message_data = schemas.MessageCreate(
            telegram_message_id=event.message.id,
            # We no longer need to pass channel_telegram_id here, as it's in channel_data
            content=event.raw_text,
            sent_at=event.message.date,
        )
        
        # Step 3: Call the service to save everything.
        # `db_message` is a safe Pydantic schema object.
        message_schema = save_new_message(
            message_schema=message_data,
            channel_schema=channel_data # Pass the enriched channel data
        )

        if not message_schema:
            logger.warning("Message was not saved, skipping matching.")
            return

        # Step 4: Call the dedicated matching service.
        await run_matching_for_message(message_schema, channel_data)

    except Exception as e:
        logger.error(f"Error in process_new_message orchestrator: {e}", exc_info=True)