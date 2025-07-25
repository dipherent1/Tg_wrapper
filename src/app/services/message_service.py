# src/app/services/message_service.py

import logging
from app.repo.unit_of_work import UnitOfWork
from app.domain import models, schemas
import uuid

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
            tag = uow.tags.get_or_create_tag(name="others", description="Default tag")
            channel_orm.tags.append(tag)

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

def get_all_messages_paginated(filters: schemas.MessageFilterParams) -> tuple[int, list[schemas.MessageResponse]]:
    """Service to fetch all messages with filtering and pagination."""
    logger.info("Service: Fetching all paginated messages.")
    with UnitOfWork() as uow:
        total, messages_orm = uow.messages.get_paginated_messages(filters)
        messages_dto = [schemas.MessageResponse.model_validate(m) for m in messages_orm]
    return total, messages_dto

def add_tags_to_message(message_id: uuid.UUID, tag_names: list[str]) -> schemas.MessageResponse | None:
    """Service to add tags to a message."""
    logger.info(f"Service: Adding tags {tag_names} to message {message_id}")
    with UnitOfWork() as uow:
        message = uow.messages.get_message_by_id(message_id)
        if not message:
            return None

        tags_to_add = []
        if tag_names:
            for tag_name in tag_names:
                tag = uow.tags.get_or_create_tag(tag_name, description="")
                if tag:
                    tags_to_add.append(tag)
        else:
            # If no tags were specified, we can add a default tag.
            tag = uow.tags.get_or_create_tag(name="others", description="Default tag")
            tags_to_add.append(tag)
            
        if tags_to_add:
            for tag in tags_to_add:
                if tag not in message.tags:
                    message.tags.append(tag)


        uow.session.flush()
        response_dto = schemas.MessageResponse.model_validate(message)
    return response_dto

def delete_message_by_id(message_id: uuid.UUID) -> bool:
    """Service to delete a message by its ID."""
    logger.info(f"Service: Deleting message {message_id}")
    with UnitOfWork() as uow:
        message = uow.messages.get_message_by_id(message_id)
        if not message:
            return False
        
        uow.messages.delete_message(message)
    return True
