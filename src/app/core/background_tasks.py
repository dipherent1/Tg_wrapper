# src/app/core/background_tasks.py

import asyncio
import logging
import os
from telethon import TelegramClient
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.errors.rpcerrorlist import UserAlreadyParticipantError, FloodWaitError

JOIN_QUEUE_FILE = "join_queue.txt"

async def process_join_queue_task(client: TelegramClient):
    """
    A background task that joins channels based on usernames or invite links
    from a queue file.
    """
    logging.info(f"[Listener] Started join queue processor for session: {client.session.filename}")
    while True:
        try:
            if not os.path.exists(JOIN_QUEUE_FILE) or os.path.getsize(JOIN_QUEUE_FILE) == 0:
                await asyncio.sleep(5)
                continue

            logging.info("[Listener] Found new requests in queue file. Processing...")
            
            with open(JOIN_QUEUE_FILE, "r+") as f:
                lines = f.readlines()
                f.seek(0)
                f.truncate()

            for line in lines:
                parts = line.strip().split(',')
                identifier = parts[0]
                
                if not identifier:
                    continue

                try:
                    logging.info(f"[Listener] Processing join request for identifier '{identifier}'...")
                    
                    if 't.me/+' in identifier or 'telegram.me/+' in identifier:
                        # --- Case 1: Private invite link (t.me/+ABC...) ---
                        invite_hash = identifier.split('/')[-1].replace('+', '')
                        updates = await client(ImportChatInviteRequest(invite_hash))
                        joined_entity = updates.chats[0]
                        logging.info(f"✅ [SUCCESS] Joined private chat via invite link: '{joined_entity.title}'")
                    
                    else:
                        # # --- Case 2: Public channel (@username or t.me/username) ---
                        # # First, normalize the identifier to just the username
                        # if identifier.startswith('@'):
                        #     entity_name = identifier
                        # elif 't.me/' in identifier:
                        #     entity_name = identifier.split('/')[-1]
                        # else:
                        #     # If it's not a link or @name, assume it's a raw username
                        #     entity_name = identifier

                        # This is the correct 2-step process
                        # 1. Get the full channel object
                        # logging.info(f"[Listener] Resolving entity for '{identifier}'...")
                        # entity = await client.get_entity(identifier)
                        # logging.info(f"[Listener] Resolved entity: {entity.title} (ID: {entity.id})")
                        # 2. Join using the entity object
                        await client(JoinChannelRequest(identifier))
                        logging.info(f"✅ [SUCCESS] Joined public channel: '{identifier}'")

                except UserAlreadyParticipantError:
                    logging.warning(f"ℹ️ [INFO] Already a participant in chat: {identifier}")
                except FloodWaitError as e:
                    logging.error(f"❌ [ERROR] Flood wait error. Sleeping for {e.seconds} seconds.")
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    # This will now correctly catch errors if the entity can't be found
                    logging.error(f"❌ [ERROR] Failed to process identifier {identifier}: {e}")

        except Exception as e:
            logging.error(f"An unexpected error occurred in the processing loop: {e}")
        
        await asyncio.sleep(5)