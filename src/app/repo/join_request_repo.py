# src/app/repo/join_request_repo.py
import uuid # <-- Make sure to import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..domain import models

class JoinRequestRepo:
    def __init__(self, session: Session):
        self.session = session
    
    def create_request(self, identifier: str, tags: list[str], user_id: uuid.UUID) -> models.ChannelJoinRequest:
        req = models.ChannelJoinRequest(
            identifier=identifier,
            tags=tags,
            requested_by_user_id=user_id
        )
        self.session.add(req)
        return req
    
    # We'll need these methods for the listener later
    def get_one_pending_request(self) -> models.ChannelJoinRequest | None:
        return self.session.execute(
            select(models.ChannelJoinRequest)
            .where(models.ChannelJoinRequest.status == models.JoinRequestStatus.PENDING)
            .limit(1)
        ).scalar_one_or_none()

    def update_request_status(self, request_id: uuid.UUID, status: models.JoinRequestStatus):
        # This method needs to be implemented to update the status
        request = self.session.get(models.ChannelJoinRequest, request_id)
        if request:
            request.status = status