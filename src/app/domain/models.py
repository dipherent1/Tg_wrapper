from sqlalchemy import Column, Integer, String, BigInteger, ForeignKey, Table, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.config.db import Base

# Association Table for the many-to-many relationship between channels and tags
channel_tags = Table('channel_tags', Base.metadata,
    Column('channel_id', Integer, ForeignKey('channels.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class Channel(Base):
    __tablename__ = "channels"

    id = Column(Integer, primary_key=True, index=True)
    telegram_channel_id = Column(BigInteger, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    type = Column(String, nullable=True) # 'channel' or 'supergroup'
    
    # Many-to-Many relationship with Tag
    tags = relationship("Tag", secondary=channel_tags, back_populates="channels")

class Tag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    # Many-to-Many relationship with Channel
    channels = relationship("Channel", secondary=channel_tags, back_populates="tags")

# NEW: Add the User model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_user_id = Column(BigInteger, unique=True, nullable=False, index=True)
    first_name = Column(String)
    username = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # We will add a relationship to subscriptions later
    # subscriptions = relationship("Subscription", back_populates="user")