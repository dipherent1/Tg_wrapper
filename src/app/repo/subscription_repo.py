# src/app/repo/subscription_repo.py

import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from ..domain import models, schemas

class SubscriptionRepo:
    def __init__(self, session: Session):
        self.session = session

    def create_subscription(self, schema: schemas.SubscriptionCreate) -> models.Subscription:
        new_sub = models.Subscription(**schema.model_dump())
        self.session.add(new_sub)
        return new_sub

    def get_all_active_subscriptions(self) -> list[models.Subscription]:
        return self.session.execute(
            select(models.Subscription).where(models.Subscription.status == models.Status.ACTIVE)
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