# src/app/repo/message_repo.py
from sqlalchemy.orm import Session
from ..domain import models, schemas
from .channel_repo import ChannelRepo

class MessageRepo:
    def __init__(self, session: Session):
        self.session = session
        self.channel_repo = ChannelRepo(session)

    def create_message(self, message_schema: schemas.MessageCreate, channel_orm: models.Channel) -> models.Message:
        """
        Creates a message and links it to the provided channel ORM object.
        """
        if not channel_orm:
            # This check is just for safety.
            raise ValueError("A valid Channel ORM object must be provided to create a message.")

        new_message = models.Message(
            telegram_message_id=message_schema.telegram_message_id,
            content=message_schema.content,
            sent_at=message_schema.sent_at,
            # Populate both fields from the provided channel object
            channel_id=channel_orm.id,
            channel_telegram_id=channel_orm.telegram_id
        )
        self.session.add(new_message)
        return new_message

