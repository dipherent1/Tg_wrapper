# src/app/services/subscription_service.py

import logging
import uuid
from app.repo.unit_of_work import UnitOfWork
from app.domain import models, schemas
from typing import List
import datetime

logger = logging.getLogger(__name__)

def add_subscription_for_user(user_id: uuid.UUID, query_text: str, tag_names: List[str]) -> models.Subscription:
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

        tags_to_add = []
        if tag_names:
            for tag_name in tag_names:
                tag = uow.tags.get_or_create_tag(name=tag_name, description="")
                if tag:
                    tags_to_add.append(tag)
        
        else:
            tag = uow.tags.get_or_create_tag(name="others", description="default tag")
                
        
        sub_schema = schemas.SubscriptionCreate(
            user_id=user_id,
            query_text=query_text,
        )

        # Use the repository to create the subscription
        subscription_orm = uow.subscriptions.create_subscription(sub_schema)
        if tags_to_add:
            for tag in tags_to_add:
                if tag not in subscription_orm.tags:
                    subscription_orm.tags.append(tag)


        # Flush the session to get the DB-generated defaults (id, created_at, etc.)
        uow.session.flush()
        uow.session.refresh(subscription_orm)

    # The UoW commits automatically upon exiting the 'with' block.
    return subscription_orm

def get_user_subscriptions(user_id: uuid.UUID) -> list[schemas.Subscription]:
    """Service to fetch all active subscriptions for a user, returning Pydantic models."""
    logger.info(f"Service: Fetching subscriptions for user_id {user_id}")
    
    with UnitOfWork() as uow:
        # Get the list of ORM objects
        subs_orm = uow.subscriptions.get_active_subscriptions_for_user(user_id)
        
        # --- THE FIX ---
        # Convert each ORM object into a Pydantic schema WHILE THE SESSION IS OPEN.
        subs_dto = [schemas.Subscription.model_validate(sub) for sub in subs_orm]

    # Return the list of safe, detached Pydantic objects.
    return subs_dto

def cancel_subscription(user_id: uuid.UUID, subscription_id: uuid.UUID) -> bool:
    """
    Core business logic to cancel a subscription.
    Ensures that the user owns the subscription they are trying to cancel.
    
    Returns:
        True if cancellation was successful, False otherwise.
    """
    logger.info(f"Service: Attempting to cancel subscription {subscription_id} for user {user_id}")
    with UnitOfWork() as uow:
        # Step 1: Fetch the subscription by its ID
        subscription = uow.subscriptions.get_subscription_by_id(subscription_id)

        # Step 2: Validate ownership and status
        if not subscription:
            logger.warning(f"Subscription {subscription_id} not found.")
            return False
        if subscription.user_id != user_id:
            logger.error(f"SECURITY: User {user_id} tried to cancel subscription {subscription_id} owned by {subscription.user_id}.")
            return False
        if subscription.status != models.Status.ACTIVE:
            logger.warning(f"Subscription {subscription_id} is not active, cannot cancel.")
            return False

        # Step 3: Perform the soft delete
        uow.subscriptions.soft_delete_subscription(subscription)
        
        # UoW will commit the status change upon exit.
    
    return True


def edit_subscription(user_id: uuid.UUID, subscription_id: uuid.UUID, new_query_text: str) -> bool:
    """
    Core business logic to edit a subscription's query text.
    Ensures the user owns the subscription they are trying to edit.
    
    Returns:
        True if the edit was successful, False otherwise.
    """
    logger.info(f"Service: Attempting to edit subscription {subscription_id} for user {user_id}")

    if not new_query_text or len(new_query_text) < 3:
        logger.warning("Edit failed: New query text is too short.")
        return False

    with UnitOfWork() as uow:
        # Step 1: Fetch the subscription
        subscription = uow.subscriptions.get_subscription_by_id(subscription_id)

        # Step 2: Validate ownership and status
        if not subscription:
            logger.warning(f"Subscription {subscription_id} not found.")
            return False
        if subscription.user_id != user_id:
            logger.error(f"SECURITY: User {user_id} tried to edit subscription owned by {subscription.user_id}.")
            return False
        if subscription.status != models.Status.ACTIVE:
            logger.warning(f"Subscription {subscription_id} is not active, cannot edit.")
            return False

        # Step 3: Perform the update
        uow.subscriptions.update_subscription_query(subscription, new_query_text)
        # UoW will commit the changes upon exit.
    
    return True

def get_all_subscriptions_paginated(
    filters: schemas.SubscriptionFilterParams
) -> tuple[int, list[schemas.SubscriptionResponse]]:
    """
    Service to fetch all subscriptions with filtering and pagination.
    Accepts a filter parameter object.
    """
    logger.info("Service: Fetching all paginated subscriptions.")
    with UnitOfWork() as uow:
        total, subs_orm = uow.subscriptions.get_paginated_subscriptions(
            filters=filters
        )
        subs_dto = [schemas.SubscriptionResponse.model_validate(s) for s in subs_orm]
    return total, subs_dto



# --- NEW SERVICE FUNCTION FOR THE API ---
def add_tags_to_subscription(sub_id: uuid.UUID, tag_names: list[str]) -> schemas.SubscriptionResponse | None:
    """
    Service to add tags to a subscription. It orchestrates both the
    SubscriptionRepo and the TagRepo.
    """
    logger.info(f"Service: Adding tags {tag_names} to subscription {sub_id}")
    with UnitOfWork() as uow:
        # Step 1: Get the subscription
        subscription = uow.subscriptions.get_subscription_by_id(sub_id)
        if not subscription:
            return None

        # Step 2: Get the tag objects
        tags_to_add = []
        if tag_names:
            for tag_name in tag_names:
                tag = uow.tags.get_or_create_tag(tag_name, description="")
                if tag:
                    tags_to_add.append(tag)
        
        else:
            # If no tags were specified, we can add a default tag.
            tag = uow.tags.get_or_create_tag(name="others", description="Default tag")
            tags_to_add.append(tag)

        # Step 3: Append the new tags
        for tag in tags_to_add:
            if tag not in subscription.tags:
                subscription.tags.append(tag)
        
        uow.session.flush()
        response_dto = schemas.SubscriptionResponse.model_validate(subscription)

    return response_dto
