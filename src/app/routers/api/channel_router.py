# src/app/routers/channels_api.py

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from app.domain import schemas
from app.services import channel_service

channel_router = APIRouter(prefix="/channels", tags=["Channels API"])

@channel_router.get("/", response_model=schemas.PaginatedResponse[schemas.Channel])
def get_all_channels(filters: schemas.ChannelFilterParams = Depends()):
    """Get a paginated list of all monitored channels with advanced filtering."""
    total, channels_dto = channel_service.get_all_channels_paginated(filters)
    return schemas.PaginatedResponse(total=total, limit=filters.limit, skip=filters.skip, items=channels_dto)

@channel_router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def leave_channel(channel_id: uuid.UUID):
    """
    Instructs the listener to leave a channel/group and deletes it from the database.
    """
    # This endpoint must be async because our service function is now async.
    success = await channel_service.leave_channel(channel_id)
    if not success:
        raise HTTPException(status_code=404, detail="Channel not found in database.")

@channel_router.post("/{channel_id}/tags", response_model=schemas.Channel)
def add_tags_to_channel(channel_id: uuid.UUID, request: schemas.AddTagsRequest):
    """Adds one or more tags to an existing channel."""
    updated_channel = channel_service.add_tags_to_channel(channel_id, request.tag_names)
    if not updated_channel:
        raise HTTPException(status_code=404, detail="Channel not found.")
    return updated_channel