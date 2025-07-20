# src/app/services/user_service.py

import logging
from telegram import User as TelegramUser # Use an alias to avoid name clashes
from app.repo.unit_of_work import UnitOfWork
from app.domain import models, schemas

logger = logging.getLogger(__name__)

def get_or_create_user(telegram_user: TelegramUser) -> models.User:
    """
    The single, reusable service for getting or creating a user.
    Takes a telegram.User object and returns our database User model.
    """
    logger.info(f"Service: Getting or creating user {telegram_user.id} ({telegram_user.full_name})")
    
    # Create the Pydantic schema from the Telegram User object
    user_schema = schemas.UserCreate(
        telegram_id=telegram_user.id,
        full_name=telegram_user.full_name,
        username=telegram_user.username,
    )

    with UnitOfWork() as uow:
        db_user = uow.users.get_or_create_user(user_schema)
        # We need to make a copy of the data before the session closes
        # Using a Pydantic model is the cleanest way.
        uow.session.flush()

        user_dto = schemas.User.model_validate(db_user)

    # Return the Pydantic model, which is a safe, detached copy of the data.
    return user_dto