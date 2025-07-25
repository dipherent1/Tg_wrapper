# src/app/repo/channel_repo.py

from sqlalchemy.orm import Session
from sqlalchemy import select
from ..domain import models, schemas
from .tag_repo import TagRepo
from sqlalchemy.orm import selectinload
from sqlalchemy import func, or_
import uuid

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
            channel.type = schema.type or channel.type
            return channel
        
        new_channel = models.Channel(**schema.model_dump())
        self.session.add(new_channel)
        return new_channel

    def add_tags_to_channel(self, channel: models.Channel, tag: models.Tag):
        """
        Associates a list of tags with a channel. Creates tags if they don't exist.
        This is the correct ORM way to handle many-to-many relationships.
        """
        
        if tag not in channel.tags:
            channel.tags.append(tag)
    
    
    def get_channel_by_id(self, channel_id: uuid.UUID) -> models.Channel | None:
        """Gets a single channel by its primary key (UUID)."""
        return self.session.get(models.Channel, channel_id)

    def get_paginated_channels(self, filters: schemas.ChannelFilterParams) -> tuple[int, list[models.Channel]]:
        """A powerful query method for channels with filtering and pagination."""
        stmt = (
            select(models.Channel)
            .options(selectinload(models.Channel.tags)) # Eager load tags
            .order_by(models.Channel.name)
        )

        if filters.search:
            # Search in both name and username
            search_term = f"%{filters.search}%"
            stmt = stmt.where(
                or_(
                    models.Channel.name.ilike(search_term),
                    models.Channel.username.ilike(search_term)
                )
            )
        if filters.tags:
            stmt = stmt.join(models.Channel.tags).where(models.Tag.name.in_(filters.tags))
        if filters.channel_id:
            stmt = stmt.where(models.Channel.id == filters.channel_id)
        if filters.channel_telegram_id:
            stmt = stmt.where(models.Channel.telegram_id == filters.channel_telegram_id)
        if filters.type:
            stmt = stmt.where(models.Channel.type == filters.type)
        if filters.status:
            stmt = stmt.where(models.Channel.status == filters.status)
            

        total_count = self.session.scalar(select(func.count()).select_from(stmt.subquery()))
        
        paginated_stmt = stmt.offset(filters.skip).limit(filters.limit)
        items = self.session.execute(paginated_stmt).scalars().unique().all()
        
        return total_count, items

    def delete_channel(self, channel: models.Channel):
        """
        Deletes a channel. The DB's ON DELETE rules will handle setting
        message foreign keys to NULL and cascading deletes to channel_tags.
        """
        self.session.delete(channel)
