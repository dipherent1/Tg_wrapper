# src/app/services/channel_service.py

import logging
from app.repo.unit_of_work import UnitOfWork
from app.domain import schemas
import uuid

# Set up a logger for this service
logger = logging.getLogger(__name__)

def add_channel_with_tags(channel_schema: schemas.ChannelCreate, tag_names: list[str]) -> schemas.Channel:
    """
    The core, reusable business logic for adding a channel and associating it with tags.
    This function is completely independent of the bot or any other interface.
    
    Args:
        channel_schema: Pydantic schema with the new channel's data.
        tag_names: A list of strings representing the tags to add.
        
    Returns:
        A Pydantic schema of the newly created (or updated) channel with its tags.
    """
    logger.info(f"Service: Adding channel '{channel_schema.name or channel_schema.telegram_id}' with tags: {tag_names}")
    
    # The 'with' statement handles the entire transaction lifecycle.
    with UnitOfWork() as uow:
        # Step 1: Get or create the channel using the repository.
        channel_orm = uow.channels.get_or_create_channel(channel_schema)
        
        # Step 2: Add the specified tags to the channel.
        # The repository handles the logic of finding/creating tags and linking them.
        if tag_names:
            for tag_name in tag_names:
                tag = uow.tags.get_or_create_tag(name=tag_name, description="")
                if tag:
                    channel_orm.tags.append(tag)
        else:
            # If no tags were specified, we can add a default tag.
            tag = uow.tags.get_or_create_tag(name="others", description="Default tag")
            channel_orm.tags.append(tag)
    
        uow.session.flush()

        # To return the full object with tags loaded, we can convert it to our Pydantic schema.
        # The ORM object might expire after the session closes, but the Pydantic model is a safe, static copy.
        channel_dto = schemas.Channel.model_validate(channel_orm)
    
    return channel_dto

def get_all_channels_paginated(filters: schemas.ChannelFilterParams) -> tuple[int, list[schemas.Channel]]:
    """Service to fetch all channels with filtering and pagination."""
    logger.info("Service: Fetching all paginated channels.")
    with UnitOfWork() as uow:
        total, channels_orm = uow.channels.get_paginated_channels(filters)
        channels_dto = [schemas.Channel.model_validate(c) for c in channels_orm]
    return total, channels_dto

def leave_channel(channel_id: uuid.UUID) -> None:
    """
    Service to leave a channel.
    This will inactivate the channel record, which will also handle the inactivation of associated messages and tags.
    """
    logger.info(f"Service: Leaving channel with ID {channel_id}.")
    with UnitOfWork() as uow:
        channel = uow.channels.get_channel_by_id(channel_id)
        if not channel:
            logger.warning(f"Channel with ID {channel_id} not found.")
            return
        
        channel.status = schemas.Status.INACTIVE
        uow.session.flush()
        uow.session.refresh(channel)
        logger.info(f"Successfully left channel with ID {channel_id}.")


def add_tags_to_channel(channel_id: uuid.UUID, tag_names: list[str]) -> schemas.Channel | None:
    """
    Service to add tags to a channel. It orchestrates both the ChannelRepo and the TagRepo.
    
    Args:
        channel_id: The UUID of the channel to which tags will be added.
        tag_names: A list of strings representing the tag names to add.
        
    Returns:
        A Pydantic schema of the updated channel with its tags, or None if the channel was not found.
    """
    logger.info(f"Service: Adding tags {tag_names} to channel {channel_id}")
    with UnitOfWork() as uow:
        # Step 1: Get the channel
        channel = uow.channels.get_channel_by_id(channel_id)
        if not channel:
            logger.warning(f"Channel with ID {channel_id} not found.")
            return None

        # Step 2: Get or create the tag objects
        tags_to_add = []
        for tag_name in tag_names:
            tag = uow.tags.get_or_create_tag(name=tag_name, description="")
            if tag:
                tags_to_add.append(tag)

        # Step 3: Append the new tags
        for tag in tags_to_add:
            if tag not in channel.tags:
                channel.tags.append(tag)
        
        uow.session.flush()
    
    return schemas.Channel.model_validate(channel)
