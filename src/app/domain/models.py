# src/app/domain/models.py

import uuid
from sqlalchemy import (
    Column, String, BigInteger, ForeignKey, Table, DateTime, Text, Boolean, ARRAY,
    Enum as SQLAlchemyEnum
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.config.db import Base
import enum
from typing import Optional

# --- Enums for Status Fields ---
# Using enums makes the status field much more robust and readable.
class Status(enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELETED = "deleted"

class ChatType(enum.Enum):
    CHANNEL = "channel"
    SUPERGROUP = "supergroup"
    BASIC_GROUP = "basic_group"

# --- Association Table for Many-to-Many Relationships ---
# We'll use the modern Mapped[] syntax for these too.
channel_tags_table = Table(
    'channel_tags',
    Base.metadata,
    Column(
        'channel_id', 
        UUID(as_uuid=True), 
        # Add ondelete="CASCADE" here
        ForeignKey('channels.id', ondelete="CASCADE"), 
        primary_key=True
    ),
    Column(
        'tag_id', 
        UUID(as_uuid=True), 
        # And also add it here for completeness when deleting tags
        ForeignKey('tags.id', ondelete="CASCADE"), 
        primary_key=True
    )
)


subscription_tags_table = Table(
    'subscription_tags',
    Base.metadata,
    Column('subscription_id', UUID(as_uuid=True), ForeignKey('subscriptions.id', ondelete="CASCADE"), primary_key=True),
    Column('tag_id', UUID(as_uuid=True), ForeignKey('tags.id', ondelete="CASCADE"), primary_key=True)
)

message_tags_table = Table(
    'message_tags',
    Base.metadata,
    Column('message_id', UUID(as_uuid=True), ForeignKey('messages.id', ondelete="CASCADE"), primary_key=True),
    Column('tag_id', UUID(as_uuid=True), ForeignKey('tags.id', ondelete="CASCADE"), primary_key=True)
)


# --- Core Models ---

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    
    status: Mapped[Status] = mapped_column(SQLAlchemyEnum(Status), default=Status.ACTIVE, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    subscriptions: Mapped[list["Subscription"]] = relationship(back_populates="user")
    join_requests: Mapped[list["ChannelJoinRequest"]] = relationship(back_populates="requested_by")


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # --- NEW: Add a username field ---
    # This is crucial for generating public links. We'll populate it when we can.
    username: Mapped[str | None] = mapped_column(String, nullable=True, unique=True, index=True)
    type: Mapped[ChatType] = mapped_column(SQLAlchemyEnum(ChatType), nullable=True)
    
    status: Mapped[Status] = mapped_column(SQLAlchemyEnum(Status), default=Status.ACTIVE, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    messages: Mapped[list["Message"]] = relationship(back_populates="channel")
    tags: Mapped[list["Tag"]] = relationship(
        secondary=channel_tags_table, 
        back_populates="channels"
    )


    # TODO: Consider adding fields for approval status and privacy (e.g., approved)

    @property
    def clickable_link(self) -> str | None:
        """
        Generates a clickable t.me link for the channel.
        Returns a public link if the channel has a username, otherwise returns None.
        """
        if self.username:
            return f"https://t.me/{self.username}"
        return None

class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    #TODO add description field for tags
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    
    # Relationships
    channels: Mapped[list["Channel"]] = relationship(secondary=channel_tags_table, back_populates="tags")
    subscriptions: Mapped[list["Subscription"]] = relationship(secondary=subscription_tags_table, back_populates="tags")
    messages: Mapped[list["Message"]] = relationship(secondary=message_tags_table, back_populates="tags")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    
    status: Mapped[Status] = mapped_column(SQLAlchemyEnum(Status), default=Status.ACTIVE, nullable=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user: Mapped["User"] = relationship(back_populates="subscriptions")
    tags: Mapped[list["Tag"]] = relationship(secondary=subscription_tags_table, back_populates="subscriptions")

class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    telegram_message_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    channel_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("channels.id", ondelete="SET NULL"), 
        nullable=True, 
        index=True
    )
    channel_telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)

    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    
    
    sent_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=False)
    
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    channel: Mapped[Optional["Channel"]] = relationship(back_populates="messages")
    tags: Mapped[list["Tag"]] = relationship(secondary=message_tags_table, back_populates="messages")

    
    @property
    def clickable_link(self) -> str:
        """
        Generates a clickable t.me link for the message.
        Handles public and private channels/supergroups.
        Returns a non-link placeholder for basic groups.
        """
        # A channel/supergroup ID is always less than -1000000000000
        is_supergroup_or_channel = (self.channel_telegram_id < -1_000_000_000_000)

        if is_supergroup_or_channel:
            # For supergroups and channels, the link format is t.me/c/...
            simple_channel_id = abs(self.channel_telegram_id) - 1_000_000_000_000
            return f"https://t.me/c/{simple_channel_id}/{self.telegram_message_id}"
        else:
            # Basic groups do not have a standard, constructible public link to a specific message.
            # We return a link to the chat itself, which is the best we can do.
            # Note: This link might not work on all clients for private basic groups.
            return f"https://t.me/c/{abs(self.channel_telegram_id)}/{self.telegram_message_id}"
# In src/app/domain/models.py
class JoinRequestStatus(enum.Enum):
    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"

class ChannelJoinRequest(Base):
    __tablename__ = "channel_join_requests"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # This will store the @username, t.me link, or raw ID
    identifier: Mapped[str] = mapped_column(String, index=True)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String)) # Store tags as an array of strings
    requested_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    status: Mapped[JoinRequestStatus] = mapped_column(SQLAlchemyEnum(JoinRequestStatus), default=JoinRequestStatus.PENDING)
    created_at: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    requested_by: Mapped["User"] = relationship(back_populates="join_requests")

    # TODO: Consider adding fields for approval status and privacy (e.g., approved)
