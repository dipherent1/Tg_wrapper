# src/app/services/message_service.py

import logging
from app.repo.unit_of_work import UnitOfWork
from app.domain import models, schemas

logger = logging.getLogger(__name__)

# --- THIS IS THE UPDATED FUNCTION SIGNATURE ---
def save_new_message(message_schema: schemas.MessageCreate, channel_schema: schemas.ChannelCreate) -> schemas.Message | None:
    """
    Saves a new message and ensures its parent channel exists with full details.
    """
    logger.info(f"Service: Saving message for channel '{channel_schema.name or channel_schema.telegram_id}'")
    
    with UnitOfWork() as uow:
        # Step 1: Get or create the channel ORM object.
        channel_orm = uow.channels.get_or_create_channel(channel_schema)

        if not channel_orm.tags:
            uow.channels.add_tags_to_channel(channel=channel_orm, tag_names=["default"])
        
        # --- THIS IS THE FIX ---
        # Step 2: Pass the message schema AND the channel ORM object to the repo.
        # The repo no longer needs to look up the channel itself.
        db_message = uow.messages.create_message(
            message_schema=message_schema,
            channel_orm=channel_orm
        )

        uow.session.flush()
        message_dto = schemas.Message.model_validate(db_message)

    return message_dto
