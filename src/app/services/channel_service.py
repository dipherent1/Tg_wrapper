# src/app/services/channel_service.py

import logging
from app.repo.unit_of_work import UnitOfWork
from app.domain import schemas

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
                    uow.channels.add_tags_to_channel(channel=channel_orm, tag=tag)

        # The UnitOfWork will automatically commit the session when the 'with' block exits.
        # This saves the channel and the tags/links in a single atomic transaction.
        uow.session.flush()

        # To return the full object with tags loaded, we can convert it to our Pydantic schema.
        # The ORM object might expire after the session closes, but the Pydantic model is a safe, static copy.
        channel_dto = schemas.Channel.model_validate(channel_orm)
    
    return channel_dto