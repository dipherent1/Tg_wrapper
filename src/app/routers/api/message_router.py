# src/app/routers/messages_api.py

import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from app.domain import schemas
from app.services import message_service

message_router = APIRouter(prefix="/messages", tags=["Messages API"])

@message_router.get("/", response_model=schemas.PaginatedResponse[schemas.MessageResponse])
def get_all_messages(filters: schemas.MessageFilterParams = Depends()):
    """Get a paginated list of all messages with advanced filtering."""
    total, messages_dto = message_service.get_all_messages_paginated(filters)
    return schemas.PaginatedResponse(total=total, limit=filters.limit, skip=filters.skip, items=messages_dto)

@message_router.delete("/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(message_id: uuid.UUID):
    """Permanently deletes a message."""
    success = message_service.delete_message_by_id(message_id)
    if not success:
        raise HTTPException(status_code=404, detail="Message not found.")

@message_router.post("/{message_id}/tags", response_model=schemas.MessageResponse)
def add_tags_to_message(message_id: uuid.UUID, request: schemas.AddTagsRequest):
    """Adds one or more tags to an existing message."""
    updated_message = message_service.add_tags_to_message(message_id, request.tag_names)
    if not updated_message:
        raise HTTPException(status_code=404, detail="Message not found.")
    return updated_message