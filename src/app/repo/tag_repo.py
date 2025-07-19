# src/app/repo/tag_repo.py

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

    def get_or_create_tag(self, name: str) -> models.Tag:
        """Finds a tag by name or creates it if it doesn't exist."""
        tag = self.get_tag_by_name(name)
        if tag:
            return tag
        
        new_tag = models.Tag(name=name)
        self.session.add(new_tag)
        # NO COMMIT HERE. The service layer will commit.
        return new_tag