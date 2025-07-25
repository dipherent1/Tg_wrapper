# src/app/repo/subscription_repo.py

import uuid
from sqlalchemy.orm import Session
from sqlalchemy import func, select, update
from ..domain import models, schemas
from sqlalchemy.orm import selectinload # <-- Add this import
import datetime

class SubscriptionRepo:
    def __init__(self, session: Session):
        self.session = session

    def create_subscription(self, schema: schemas.SubscriptionCreate) -> models.Subscription:
        new_sub = models.Subscription(**schema.model_dump())
        self.session.add(new_sub)
        return new_sub

    def get_all_active_subscriptions(self) -> list[models.Subscription]:
        """The core method for the matching engine. Eagerly loads the user relationship."""
        return self.session.execute(
            select(models.Subscription)
            .where(models.Subscription.status == models.Status.ACTIVE)
            .options(selectinload(models.Subscription.user)) # <-- The magic line
        ).scalars().all()

    # --- NEW FUNCTION ---
    def get_active_subscriptions_for_user(self, user_id: uuid.UUID) -> list[models.Subscription]:
        """Finds all active subscriptions belonging to a specific user."""
        return self.session.execute(
            select(models.Subscription)
            .where(models.Subscription.user_id == user_id)
            .where(models.Subscription.status == models.Status.ACTIVE)
        ).scalars().all()

    # --- NEW FUNCTION ---
    def get_subscription_by_id(self, subscription_id: uuid.UUID) -> models.Subscription | None:
        """Gets a single subscription by its primary key."""
        return self.session.get(models.Subscription, subscription_id)

    # --- NEW FUNCTION ---
    def soft_delete_subscription(self, subscription: models.Subscription):
        """Changes a subscription's status to DELETED instead of removing it."""
        subscription.status = models.Status.DELETED
        # The change is added to the session, to be committed by the UoW.
        
    def update_subscription_query(self, subscription: models.Subscription, new_query_text: str):
        """Updates the query_text of a given subscription object."""
        subscription.query_text = new_query_text
        subscription.updated_at = models.func.now()  # Update the timestamp

    def get_paginated_subscriptions(
        self,
        filters: schemas.SubscriptionFilterParams
    ) -> tuple[int, list[models.Subscription]]:
        """A powerful query method with filtering and pagination. Results are sorted from newest to oldest."""
        
        stmt = (
            select(models.Subscription)
            .options(selectinload(models.Subscription.tags)) # Eager load tags
            .order_by(models.Subscription.created_at.desc()) # Newest to oldest
        )

        if filters.search:
            stmt = stmt.where(models.Subscription.query_text.ilike(f"%{filters.search}%"))
        if filters.start_date:
            stmt = stmt.where(models.Subscription.created_at >= filters.start_date)
        if filters.end_date:
            # Add one day to end_date to make it inclusive
            stmt = stmt.where(models.Subscription.created_at < filters.end_date + datetime.timedelta(days=1))
        if filters.tags:
            stmt = stmt.join(models.Subscription.tags).where(models.Tag.name.in_(filters.tags))
        if filters.subscription_id:
            stmt = stmt.where(models.Subscription.id == filters.subscription_id)

        # First, get the total count of items that match the filter
        total_count = self.session.scalar(select(func.count()).select_from(stmt.subquery()))
        
        # Then, apply pagination to the main query
        paginated_stmt = stmt.offset(filters.skip).limit(filters.limit)
        items = self.session.execute(paginated_stmt).scalars().all()
        
        return total_count, items
