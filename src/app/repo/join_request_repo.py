# src/app/repo/join_request_repo.py
import uuid # <-- Make sure to import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..domain import models

class JoinRequestRepo:
    def __init__(self, session: Session):
        self.session = session
    
    def create_request(self, identifier: str, tags: list[str], user_id: uuid.UUID) -> tuple[models.ChannelJoinRequest | None, bool]:
        """
        Creates a new join request ONLY if a similar one doesn't already exist.
        The identifier passed here should be the *normalized* identifier.
        Returns the request object and a boolean indicating if it was newly created.
        """
        # --- THE DUPLICATE CHECK ---
        existing_request = self.get_existing_request(identifier)
        if existing_request:
            # A pending or successful request already exists. Do nothing new.
            # Return the existing request and False to indicate nothing was created.
            return existing_request, False
            
        # No existing request found, so create a new one.
        new_req = models.ChannelJoinRequest(
            identifier=identifier,
            tags=tags,
            requested_by_user_id=user_id
        )
        self.session.add(new_req)
        # Return the new request and True.
        return new_req, True
    
    def get_existing_request(self, normalized_identifier: str) -> models.ChannelJoinRequest | None:
        """
        Checks for a non-failed request with the given normalized identifier.
        This is the key method for preventing duplicate requests.
        """
        return self.session.execute(
            select(models.ChannelJoinRequest)
            .where(models.ChannelJoinRequest.identifier == normalized_identifier)
            # --- THIS IS THE FIX ---
            # The status must be IN the list of non-failed statuses.
            # This prevents creating a new request if one is already pending OR successful.
            .where(models.ChannelJoinRequest.status.in_([
                models.JoinRequestStatus.PENDING,
                models.JoinRequestStatus.SUCCESS
            ]))
        ).scalar_one_or_none()

    
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