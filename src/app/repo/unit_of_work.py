# src/app/repo/unit_of_work.py

from sqlalchemy.orm import Session
from app.config.db import SessionLocal

# Import all your repository classes
from .user_repo import UserRepo
from .channel_repo import ChannelRepo
from .tag_repo import TagRepo
from .subscription_repo import SubscriptionRepo
from .message_repo import MessageRepo
from .join_request_repo import JoinRequestRepo

class UnitOfWork:
    """
    Manages the session, transactions, and provides access to repositories.
    Acts as a context manager to ensure the session is handled correctly.
    """
    def __init__(self):
        self.session: Session = SessionLocal()
        # All repositories created here will share the exact same session object
        self.users = UserRepo(self.session)
        self.channels = ChannelRepo(self.session)
        self.tags = TagRepo(self.session)
        self.subscriptions = SubscriptionRepo(self.session)
        self.messages = MessageRepo(self.session)
        self.join_requests = JoinRequestRepo(self.session)

    def __enter__(self):
        """Called when entering the 'with' statement."""
        return self

    def __exit__(self, exc_type, exc_val, traceback):
        """
        Called when exiting the 'with' statement.
        Handles commit, rollback, and closing the session.
        """
        if exc_type:  # If an exception occurred
            print(f"An exception occurred: {exc_val}. Rolling back.")
            self.session.rollback()
        else:
            print("Committing changes.")
            self.session.commit()
        
        self.session.close()

    def commit(self):
        """Explicitly commits the transaction."""
        self.session.commit()

    def rollback(self):
        """Explicitly rolls back the transaction."""
        self.session.rollback()