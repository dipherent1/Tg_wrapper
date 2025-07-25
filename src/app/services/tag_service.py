# src/app/services/tag_service.py

import logging
import uuid
from app.repo.unit_of_work import UnitOfWork
from app.domain import models, schemas

logger = logging.getLogger(__name__)

def create_tag(tag: schemas.TagCreate) -> schemas.Tag:
    """Service to create a new tag."""
    logger.info(f"Service: Creating tag with name '{tag.name}' and description '{tag.description}'")
    with UnitOfWork() as uow:
        tag = uow.tags.get_or_create_tag(name=tag.name, description=tag.description)
        uow.session.flush()
        tag_dto = schemas.Tag.model_validate(tag)
    return tag_dto


def get_all_tags() -> list[schemas.Tag]:
    """Service to fetch all tags."""
    logger.info("Service: Fetching all tags.")
    with UnitOfWork() as uow:
        tags_orm = uow.tags.get_all_tags()
        tags_dto = [schemas.Tag.model_validate(tag) for tag in tags_orm]
    return tags_dto

def update_tag_description(tag_id: uuid.UUID, description: str) -> schemas.Tag | None:
    """Service to update a tag's description."""
    logger.info(f"Service: Updating description for tag {tag_id}")
    with UnitOfWork() as uow:
        tag = uow.tags.get_tag_by_id(tag_id)
        if not tag:
            return None
        
        updated_tag = uow.tags.update_tag_description(tag, description)
        uow.session.flush()
        tag_dto = schemas.Tag.model_validate(updated_tag)
    return tag_dto

def delete_tag_by_id(tag_id: uuid.UUID) -> bool:
    """Service to delete a tag by its ID."""
    logger.info(f"Service: Deleting tag {tag_id}")
    with UnitOfWork() as uow:
        tag = uow.tags.get_tag_by_id(tag_id)
        if not tag:
            return False
        
        uow.tags.delete_tag(tag)
    return True