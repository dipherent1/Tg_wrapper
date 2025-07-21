# src/app/core/worker.py

import logging
from telethon import events
from telethon.tl.types import Channel as TelethonChannel, User as TelethonUser
from app.domain import schemas

from app.services.message_service import save_new_message
from app.services.matching_service import run_matching_for_message

logger = logging.getLogger(__name__)

async def process_new_message(event: events.NewMessage.Event):
    """
    The orchestrator function. It extracts all necessary data and
    calls the appropriate services.
    """
    try:
        if not event.raw_text:
            return

        # --- THIS IS THE FIX ---
        # Step 1: Extract all available information from the event object.
        chat = await event.get_chat()
        
        # We are only interested in channels and supergroups for now.
        if not isinstance(chat, (TelethonChannel)):
             logger.debug(f"Ignoring message from non-channel chat: {getattr(chat, 'title', chat.id)}")
             return
        
        channel_name = getattr(chat, 'title', None)
        channel_username = getattr(chat, 'username', None)

        # Step 2: Create the Pydantic schemas with the enriched data.
        channel_data = schemas.ChannelCreate(
            telegram_id=event.chat_id,
            name=channel_name,
            username=channel_username
        )

        message_data = schemas.MessageCreate(
            telegram_message_id=event.message.id,
            # We no longer need to pass channel_telegram_id here, as it's in channel_data
            content=event.raw_text,
            sent_at=event.message.date,
        )
        
        # Step 3: Call the service to save everything.
        # `db_message` is a safe Pydantic schema object.
        db_message = save_new_message(
            message_schema=message_data,
            channel_schema=channel_data # Pass the enriched channel data
        )
        
        if not db_message:
            logger.warning("Message was not saved, skipping matching.")
            return

        # Step 4: Call the dedicated matching service.
        # await run_matching_for_message(db_message)

    except Exception as e:
        logger.error(f"Error in process_new_message orchestrator: {e}", exc_info=True)