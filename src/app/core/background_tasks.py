# src/app/core/background_tasks.py

import asyncio
import logging
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.errors.rpcerrorlist import UserAlreadyParticipantError, FloodWaitError
from app.repo.unit_of_work import UnitOfWork
from app.domain import models, schemas
from app.services.channel_service import add_channel_with_tags

logger = logging.getLogger(__name__)

async def process_join_requests_task(client: TelegramClient):
    """
    The main background worker task. Periodically fetches pending join requests
    from the database and processes them.
    """
    logger.info("[Processor] Starting join request processor task...")
    while True:
        try:
            pending_request = None
            with UnitOfWork() as uow:
                # Fetch one pending request to process
                # You'd add a `get_one_pending` method to your JoinRequestRepo
                pending_request = uow.join_requests.get_one_pending_request()
                if pending_request:
                    logger.info(f"Fetched pending request: {pending_request}")
                    continue
                    # Mark it as "processing" to prevent other workers from picking it up
                    # This is an advanced step, for now we can assume one worker.
                    pass 

            if not pending_request:
                await asyncio.sleep(10) # Wait 10 seconds if no jobs
                continue

            logger.info(f"Processing join request for identifier: {pending_request.identifier}")
            
            try:
                # --- Step 1: Use Telethon to join the channel ---
                identifier = pending_request.identifier
                
                # ... (The robust joining logic from before) ...
                if identifier.startswith('@') or 't.me/' in identifier and 't.me/+' not in identifier:
                    entity_name = identifier.split('/')[-1]
                    entity = await client.get_entity(entity_name)
                    await client(JoinChannelRequest(entity))
                elif 't.me/+' in identifier:
                    invite_hash = identifier.split('/')[-1].replace('+', '')
                    updates = await client(ImportChatInviteRequest(invite_hash))
                    entity = updates.chats[0]
                else: # Assume it's a raw ID from a private forward
                    entity = await client.get_entity(int(identifier))
                    await client(JoinChannelRequest(entity))

                logger.info(f"Successfully joined channel: '{entity.title}'")

                # --- Step 2: Call the service to save the channel and its tags ---
                channel_data = schemas.ChannelCreate(
                    telegram_id=entity.id,
                    name=entity.title,
                    username=getattr(entity, 'username', None)
                )
                
                # The service handles the "get or create tags" logic correctly
                add_channel_with_tags(
                    channel_schema=channel_data,
                    tag_names=pending_request.tags # Use the tags from the request
                )
                
                # --- Step 3: Update the request status to success ---
                with UnitOfWork() as uow:
                    uow.join_requests.update_request_status(pending_request.id, models.JoinRequestStatus.SUCCESS)

            except Exception as e:
                logger.error(f"Failed to process join request for {pending_request.identifier}: {e}")
                # --- Step 3b: Update the request status to failed ---
                with UnitOfWork() as uow:
                    uow.join_requests.update_request_status(pending_request.id, models.JoinRequestStatus.FAILED)
        
        except Exception as e:
            # Catch errors in the main loop itself
            logger.error(f"An unexpected error occurred in the processor task loop: {e}")
            await asyncio.sleep(30) # Wait longer if there's a major loop error