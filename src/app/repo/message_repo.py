# src/app/repo/message_repo.py
from sqlalchemy.orm import Session
from ..domain import models, schemas
from .channel_repo import ChannelRepo

class MessageRepo:
    def __init__(self, session: Session):
        self.session = session
        self.channel_repo = ChannelRepo(session)

    def create_message(self, schema: schemas.MessageCreate) -> models.Message | None:
        """Creates a message and links it to the correct channel."""
        # Find the parent channel using its telegram_id
        channel = self.channel_repo.get_channel_by_telegram_id(schema.channel_telegram_id)
        if not channel:
            # Or you could create the channel on the fly here
            return None 

        new_message = models.Message(
            telegram_message_id=schema.telegram_message_id,
            channel_id=channel.id, # Link using the channel's UUID primary key
            content=schema.content,
            sent_at=schema.sent_at
        )
        self.session.add(new_message)
        return new_message