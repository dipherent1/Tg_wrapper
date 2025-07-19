# src/app/repo/user_repo.py

from sqlalchemy.orm import Session
from sqlalchemy import select
from ..domain import models, schemas

class UserRepo:
    def __init__(self, session: Session):
        self.session = session

    def get_user_by_telegram_id(self, telegram_id: int) -> models.User | None:
        return self.session.execute(
            select(models.User).where(models.User.telegram_id == telegram_id)
        ).scalar_one_or_none()
    
    def get_or_create_user(self, schema: schemas.UserCreate) -> models.User:
        """Finds a user by telegram_id or creates them."""
        user = self.get_user_by_telegram_id(schema.telegram_id)
        if user:
            # If user was soft-deleted, reactivate them
            if user.status == models.Status.DELETED:
                user.status = models.Status.ACTIVE
            user.full_name = schema.full_name # Update name
            user.username = schema.username
            return user
        
        new_user = models.User(**schema.model_dump())
        self.session.add(new_user)
        return new_user