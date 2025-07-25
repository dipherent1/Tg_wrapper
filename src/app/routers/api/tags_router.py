# src/app/routers/tags_api.py

import uuid
from fastapi import APIRouter, HTTPException, status
from app.domain import schemas
from app.services import tag_service

tag_router = APIRouter(prefix="/tags", tags=["Tags API"])

@tag_router.post("/", response_model=schemas.Tag)
def create_tag(tag: schemas.TagCreate):
    return tag_service.create_tag(tag)

@tag_router.get("/", response_model=list[schemas.Tag])
def get_all_tags():
    """Get a list of all available tags."""
    return tag_service.get_all_tags()

@tag_router.patch("/{tag_id}", response_model=schemas.Tag)
def update_tag(tag_id: uuid.UUID, request: schemas.TagUpdate):
    """Updates a tag's description."""
    updated_tag = tag_service.update_tag_description(tag_id, request.description)
    if not updated_tag:
        raise HTTPException(status_code=404, detail="Tag not found.")
    return updated_tag

@tag_router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tag(tag_id: uuid.UUID):
    """
    Deletes a tag. This will also remove all associations of this tag
    from channels, subscriptions, and messages due to DB-level cascades.
    """
    success = tag_service.delete_tag_by_id(tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found.")

    