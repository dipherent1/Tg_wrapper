# src/app/core/background_tasks.py

import asyncio
import logging
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.tl.types import Channel
from telethon.errors.rpcerrorlist import UserAlreadyParticipantError
from telethon.errors import FloodError
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
            # --- THIS IS THE KEY CHANGE ---
            # We will store the raw data, not the ORM object itself.
            request_id = None
            request_identifier = None
            request_tags = None

            # Use a UoW to safely fetch one pending job's data
            with UnitOfWork() as uow:
                pending_request = uow.join_requests.get_one_pending_request()
                if pending_request:
                    # Extract the data we need BEFORE the session closes
                    request_id = pending_request.id
                    request_identifier = pending_request.identifier
                    request_tags = pending_request.tags

            # If we didn't find a request, the variables will be None
            if not request_id:
                await asyncio.sleep(15) # Wait 15 seconds if no jobs
                continue

            # Now we are using simple Python types (UUID, str, list), not detached ORM objects.
            logger.info(f"Processing join request for identifier: {request_identifier}")
            
            try:
                # --- Step 1: Use Telethon to join the channel ---
                entity_name = request_identifier
                # if 't.me/' in request_identifier and 't.me/+' not in request_identifier:
                #     entity_name = request_identifier.split('/')[-1]

                # if 't.me/+' in request_identifier :
                #     invite_hash = request_identifier.split('/')[-1].replace('+', '')
                #     updates = await client(ImportChatInviteRequest(invite_hash))
                #     entity = updates.chats[0]
                invite_hash = None
                if "+" in request_identifier:
                    # This is a private channel invite link
                    invite_hash = request_identifier.replace('+', '')
                    updates = await client(ImportChatInviteRequest(invite_hash))
                    entity = updates.chats[0]
                else:
                    entity = await client.get_entity(entity_name)
                    if isinstance(entity, Channel):
                        await client(JoinChannelRequest(entity))
                
                logger.info(f"Successfully joined/verified channel: '{entity.title}'")

                # --- Step 2: Call the service to save the channel and tags ---
                channel_data = schemas.ChannelCreate(
                    telegram_id=entity.id,
                    name=entity.title,
                    username=getattr(entity, 'username', None),
                )
                
                add_channel_with_tags(
                    channel_schema=channel_data,
                    tag_names=request_tags # Use the tags we safely extracted
                )
                
                # --- Step 3: Update the request status to success ---
                with UnitOfWork() as uow:
                    # We now use the ID to update the request
                    uow.join_requests.update_request_status(request_id, models.JoinRequestStatus.SUCCESS)

            except UserAlreadyParticipantError:
                logger.info(f"Already a participant in channel: {request_identifier}")
                with UnitOfWork() as uow:
                    # We use the ID here too
                    uow.join_requests.update_request_status(request_id, models.JoinRequestStatus.SUCCESS)
            
            except FloodError:
                logger.warning(f"Flood error while processing {request_identifier}. Retrying after cooldown.")
                await asyncio.sleep(60)


            except Exception as e:
                logger.error(f"Failed to process join request for {request_identifier}: {e}", exc_info=True)
                with UnitOfWork() as uow:
                    # We use the ID here too
                    uow.join_requests.update_request_status(request_id, models.JoinRequestStatus.FAILED)
        
        except Exception as e:
            logger.error(f"Critical error in processor task loop: {e}", exc_info=True)
            await asyncio.sleep(60)
