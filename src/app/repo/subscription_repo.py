# src/app/repo/subscription_repo.py
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..domain import models, schemas

class SubscriptionRepo:
    def __init__(self, session: Session):
        self.session = session

    def create_subscription(self, schema: schemas.SubscriptionCreate) -> models.Subscription:
        new_sub = models.Subscription(**schema.model_dump())
        self.session.add(new_sub)
        return new_sub

    def get_all_active_subscriptions(self) -> list[models.Subscription]:
        """The core method for the matching engine."""
        return self.session.execute(
            select(models.Subscription).where(models.Subscription.status == models.Status.ACTIVE)
        ).scalars().all()
    
    # ... Add methods for listing and soft-deleting subscriptions later ...