# src/app/repo/tag_repo.py

import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..domain import models

class TagRepo:
    def __init__(self, session: Session):
        self.session = session

    def get_tag_by_name(self, name: str) -> models.Tag | None:
        return self.session.execute(
            select(models.Tag).where(models.Tag.name == name)
        ).scalar_one_or_none()

    def get_or_create_tag(self, name: str, description: str) -> models.Tag:
        """Finds a tag by name or creates it if it doesn't exist."""
        tag = self.get_tag_by_name(name)
        if tag:
            return tag

        new_tag = models.Tag(name=name, description=description)
        self.session.add(new_tag)
        # NO COMMIT HERE. The service layer will commit.
        return new_tag
    
    def get_tag_by_id(self, tag_id: uuid.UUID) -> models.Tag | None:
        """Fetches a tag by its ID."""
        return self.session.execute(
            select(models.Tag).where(models.Tag.id == tag_id)
        ).scalar_one_or_none()
    
    def get_all_tags(self) -> list[models.Tag]:
        """Gets all tags from the database."""
        return self.session.execute(select(models.Tag).order_by(models.Tag.name)).scalars().all()

    def update_tag_description(self, tag: models.Tag, description: str) -> models.Tag:
        """Updates the description of a tag."""
        tag.description = description
        return tag

    def delete_tag(self, tag: models.Tag):
        """Deletes a tag. The DB's ON DELETE CASCADE will handle associations."""
        self.session.delete(tag)