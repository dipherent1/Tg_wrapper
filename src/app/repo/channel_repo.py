# src/app/repo/channel_repo.py

from sqlalchemy.orm import Session
from sqlalchemy import select
from ..domain import models, schemas
from .tag_repo import TagRepo

class ChannelRepo:
    def __init__(self, session: Session):
        self.session = session
        self.tag_repo = TagRepo(session) # Can use other repos internally

    def get_channel_by_telegram_id(self, telegram_id: int) -> models.Channel | None:
        return self.session.execute(
            select(models.Channel).where(models.Channel.telegram_id == telegram_id)
        ).scalar_one_or_none()

    def get_or_create_channel(self, schema: schemas.ChannelCreate) -> models.Channel:
        """Finds a channel by telegram_id or creates it."""
        channel = self.get_channel_by_telegram_id(schema.telegram_id)
        if channel:
            # Optionally update name/username if it has changed
            channel.name = schema.name or channel.name
            channel.username = schema.username or channel.username
            return channel
        
        new_channel = models.Channel(**schema.model_dump())
        self.session.add(new_channel)
        return new_channel

    def add_tags_to_channel(self, channel: models.Channel, tag_names: list[str]):
        """
        Associates a list of tags with a channel. Creates tags if they don't exist.
        This is the correct ORM way to handle many-to-many relationships.
        """
        for name in tag_names:
            tag = self.tag_repo.get_or_create_tag(name)
            if tag not in channel.tags:
                channel.tags.append(tag)
    def delete_channel(self, channel: models.Channel):
        """
        Deletes a channel record. The database's ON DELETE rules will handle
        setting the foreign keys on messages to NULL and deleting the tag associations.
        """
        self.session.delete(channel)
