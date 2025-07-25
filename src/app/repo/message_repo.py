# src/app/repo/message_repo.py
from sqlalchemy.orm import Session
from ..domain import models, schemas
from .channel_repo import ChannelRepo

from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
import datetime
import uuid

class MessageRepo:
    def __init__(self, session: Session):
        self.session = session
        self.channel_repo = ChannelRepo(session)

    def create_message(self, message_schema: schemas.MessageCreate, channel_orm: models.Channel) -> models.Message:
        if not channel_orm:
            raise ValueError("A valid Channel ORM object must be provided to create a message.")

        new_message = models.Message(
            telegram_message_id=message_schema.telegram_message_id,
            content=message_schema.content,
            sent_at=message_schema.sent_at,
            channel_telegram_id=channel_orm.telegram_id,
            channel=channel_orm
        )
        self.session.add(new_message)
        return new_message

    def get_paginated_messages(self, filters: schemas.MessageFilterParams) -> tuple[int, list[models.Message]]:
        """A powerful query method for messages with filtering and pagination."""
        stmt = (
            select(models.Message)
            .options(
                selectinload(models.Message.channel), # Eager load channel
                selectinload(models.Message.tags)     # Eager load tags
            )
            .order_by(models.Message.sent_at.desc())
        )

        if filters.search:
            stmt = stmt.where(models.Message.content.ilike(f"%{filters.search}%"))
        if filters.channel_id:
            stmt = stmt.where(models.Message.channel_id == filters.channel_id)
        if filters.channel_telegram_id:
            stmt = stmt.where(models.Message.channel_telegram_id == filters.channel_telegram_id)
        if filters.message_id:
            stmt = stmt.where(models.Message.id == filters.message_id)
        if filters.start_date:
            stmt = stmt.where(models.Message.sent_at >= filters.start_date)
        if filters.end_date:
            stmt = stmt.where(models.Message.sent_at < filters.end_date + datetime.timedelta(days=1))
        if filters.tags:
            stmt = stmt.join(models.Message.tags).where(models.Tag.name.in_(filters.tags))

        total_count = self.session.scalar(select(func.count()).select_from(stmt.subquery()))
        
        paginated_stmt = stmt.offset(filters.skip).limit(filters.limit)
        items = self.session.execute(paginated_stmt).scalars().unique().all()
        
        return total_count, items

    def get_message_by_id(self, message_id: uuid.UUID) -> models.Message | None:
        return self.session.get(models.Message, message_id)

    def get_messages_by_channel_telegram_id(self, channel_telegram_id: int) -> list[models.Message]:
        return self.session.query(models.Message).filter(models.Message.channel_telegram_id == channel_telegram_id).all()

    def delete_message(self, message: models.Message):
        """Permanently deletes a message. Use with caution."""
        self.session.delete(message)


