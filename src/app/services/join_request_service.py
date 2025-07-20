# src/app/services/join_request_service.py

import logging
import uuid # Use the standard uuid library for type hinting
from app.repo.unit_of_work import UnitOfWork
from app.domain import models

logger = logging.getLogger(__name__)

def create_join_request(identifier: str, tags: list[str], user_id: uuid.UUID) -> tuple[models.ChannelJoinRequest, bool]:
    """
    Service to create a channel join request.
    Now directly returns the tuple from the repository.
    """
    logger.info(f"Service: Processing join request for '{identifier}' with tags: {tags}")
    
    with UnitOfWork() as uow:
        # The repo now handles all logic and returns the tuple.
        join_req, was_newly_created = uow.join_requests.create_request(identifier, tags, user_id)
        
        # If a request was created or found, we need to load its data before the session closes.
        if join_req:
            uow.session.flush()
            # If you need to access relationships, you might need to refresh.
            # For now, this is sufficient.

    return join_req, was_newly_created

