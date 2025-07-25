import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from app.domain import schemas
from app.services import user_service


user_router = APIRouter(prefix="/users", tags=["Users API"])

@user_router.get("/", response_model=schemas.PaginatedResponse[schemas.UserResponse])
def get_all_users(filters: schemas.UserFilterParams = Depends()):
    """Get a paginated list of all users with advanced filtering."""
    total, users_dto = user_service.get_all_users_paginated(filters)
    return schemas.PaginatedResponse(total=total, limit=filters.limit, skip=filters.skip, items=users_dto)

@user_router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(user_id: uuid.UUID):
    """Delete a user by their ID."""
    user_service.delete_user(user_id)