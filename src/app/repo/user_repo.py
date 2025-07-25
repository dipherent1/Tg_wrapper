# src/app/repo/user_repo.py

import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..domain import models, schemas
from sqlalchemy import func


class UserRepo:
    def __init__(self, session: Session):
        self.session = session

    def get_user_by_telegram_id(self, telegram_id: int) -> models.User | None:
        return self.session.execute(
            select(models.User).where(models.User.telegram_id == telegram_id)
        ).scalar_one_or_none()
    
    def get_user_by_id(self, user_id: uuid.UUID) -> models.User | None:
        return self.session.execute(
            select(models.User).where(models.User.id == user_id)
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
    
    def get_all_users_paginated(self, filters: schemas.UserFilterParams) -> tuple[int, list[models.User]]:
        """
        Get all users with advanced filtering and pagination.
        Returns a tuple of total count and a list of User models.
        """
        query = select(models.User)

        if filters.user_id:
            query = query.where(models.User.id == filters.user_id)
        if filters.telegram_id:
            query = query.where(models.User.telegram_id == filters.telegram_id)
        if filters.status:
            query = query.where(models.User.status == filters.status)
        if filters.name:
            query = query.where(models.User.full_name.ilike(f"%{filters.name}%"))
        if filters.username:
            query = query.where(models.User.username.ilike(f"%{filters.username}%"))
        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                models.User.full_name.ilike(search_term) |
                models.User.username.ilike(search_term)
            )


        total = self.session.execute(select(func.count()).select_from(query)).scalar_one()
        
        # Apply pagination
        query = query.offset(filters.skip).limit(filters.limit)
        
        users = self.session.execute(query).scalars().all()
        
        return total, users