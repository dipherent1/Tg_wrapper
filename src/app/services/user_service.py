# src/app/services/user_service.py

import logging
from telegram import User as TelegramUser # Use an alias to avoid name clashes
from app.repo.unit_of_work import UnitOfWork
from app.domain import models, schemas
import uuid
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

def get_all_users_paginated(filters: schemas.UserFilterParams) -> tuple[int, list[schemas.UserResponse]]:
    """
    Get all users with advanced filtering and pagination.
    Returns a tuple of total count and a list of UserResponse schemas.
    """
    logger.info(f"Service: Getting all users with filters {filters}")

    with UnitOfWork() as uow:
        total, users_dto = uow.users.get_all_users_paginated(filters)

        # Convert the list of database models to Pydantic schemas
        users_schemas = [schemas.UserResponse.model_validate(user) for user in users_dto]

    return total, users_schemas

def delete_user(user_id: uuid.UUID):
    """
    Delete a user by their ID.
    This will soft-delete the user by setting their status to DELETED.
    """
    logger.info(f"Service: Deleting user {user_id}")

    with UnitOfWork() as uow:
        user = uow.users.get_user_by_id(user_id)
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        # Soft delete the user
        user.status = models.Status.DELETED

    return True