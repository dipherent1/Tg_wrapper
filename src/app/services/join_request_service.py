# src/app/services/join_request_service.py

import logging
import uuid # Use the standard uuid library for type hinting
from app.repo.unit_of_work import UnitOfWork
from app.domain import models

logger = logging.getLogger(__name__)

def create_join_request(identifier: str, tags: list[str], user_id: uuid.UUID) -> models.ChannelJoinRequest:
    """
    Service to create a channel join request.
    This function is now clean and accepts the user_id directly.
    """
    logger.info(f"Service: Creating join request for '{identifier}' for user_id {user_id} with tags: {tags}")
    
    with UnitOfWork() as uow:
        # The user is already guaranteed to exist by the @ensure_user decorator.
        # We can directly use the user_id to create the request.
        
        # We assume `uow.join_requests` exists from updating the UnitOfWork class.
        join_req = uow.join_requests.create_request(
            identifier=identifier,
            tags=tags,
            user_id=user_id
        )
        
        # To be safe, we can load the request object before the session closes.
        # This is optional but good practice if you need to return the created object.
        uow.session.flush() # Flushes changes to the DB to get the object state
        uow.session.refresh(join_req)

    return join_req