# src/app/services/subscription_service.py

import logging
import uuid
from app.repo.unit_of_work import UnitOfWork
from app.domain import models, schemas

logger = logging.getLogger(__name__)

def add_subscription_for_user(user_id: uuid.UUID, query_text: str) -> models.Subscription:
    """
    Core business logic to create a new subscription for a given user.
    
    Args:
        user_id: The UUID of the user from our database.
        query_text: The text the user wants to search for.
        
    Returns:
        The newly created Subscription ORM object.
    """
    logger.info(f"Service: Adding subscription '{query_text}' for user_id {user_id}")

    with UnitOfWork() as uow:
        # Create the Pydantic schema for the new subscription
        sub_schema = schemas.SubscriptionCreate(
            user_id=user_id,
            query_text=query_text
        )

        # Use the repository to create the subscription
        subscription_orm = uow.subscriptions.create_subscription(sub_schema)

        # Flush the session to get the DB-generated defaults (id, created_at, etc.)
        uow.session.flush()
        uow.session.refresh(subscription_orm)

    # The UoW commits automatically upon exiting the 'with' block.
    return subscription_orm