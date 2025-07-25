# src/app/routers/subscriptions_api.py

from fastapi import APIRouter, HTTPException, Query, status, Depends
from app.domain import schemas
from app.services import subscription_service
import datetime
import uuid



subscription_router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])

@subscription_router.get("/", response_model=schemas.PaginatedResponse[schemas.SubscriptionResponse])
def get_all_subscriptions(filters: schemas.SubscriptionFilterParams = Depends()):
    total, subs_dto = subscription_service.get_all_subscriptions_paginated(filters=filters) # Just pass the 
    return schemas.PaginatedResponse(
        total=total, 
        limit=filters.limit, 
        skip=filters.skip, 
        items=subs_dto
    )


@subscription_router.delete("/{sub_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_subscription(sub_id: uuid.UUID, user_id: uuid.UUID = Query(...)):
    """
    Soft-deletes a subscription.
    """
    success = subscription_service.cancel_subscription(user_id=user_id, subscription_id=sub_id)
    if not success:
        raise HTTPException(status_code=404, detail="Subscription not found or user does not have permission.")

@subscription_router.post("/{sub_id}/tags", response_model=schemas.SubscriptionResponse)
def add_tags_to_subscription(sub_id: uuid.UUID, request: schemas.AddTagsRequest):
    """
    Adds one or more tags to an existing subscription.
    """
    # The router calls the service, which orchestrates the complex logic.
    updated_sub = subscription_service.add_tags_to_subscription(sub_id, request.tag_names)
    if not updated_sub:
        raise HTTPException(status_code=404, detail="Subscription not found.")
    
    return updated_sub