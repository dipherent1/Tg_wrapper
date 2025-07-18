# src/app/core/background_tasks.py

import asyncio
import logging
import os
from telethon import TelegramClient
# No need for JoinChannelRequest anymore, we use a higher-level method
from telethon.errors.rpcerrorlist import UserAlreadyParticipantError, FloodWaitError
from telethon.tl.functions.channels import JoinChannelRequest
JOIN_QUEUE_FILE = "join_queue.txt"

async def process_join_queue_task(client: TelegramClient):
    """A background task that joins channels based on usernames from a queue file."""
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
                identifier = line.strip()
                # We only expect usernames now, which should start with @
                if not identifier.startswith('@'):
                    logging.warning(f"[Listener] Skipping invalid identifier in queue: {identifier}")
                    continue

                # --- THE CORRECT AND RELIABLE METHOD ---
                try:
                    logging.info(f"[Listener] Processing join request for identifier '{identifier}'...")
                    
                    # client.join_channel() is the high-level, correct way to do this.
                    # It handles finding the entity and joining in one step.
                    joined_channel = await client(JoinChannelRequest(identifier))

                    # logging.info(f"✅ [SUCCESS] Joined channel: '{joined_channel.title}'")
                    print(f"✅ [SUCCESS] Joined channel:{identifier}")
                    logging.info(f"✅ [SUCCESS] Joined channel  ")

                except UserAlreadyParticipantError:
                    print(f"ℹ️ [INFO] Already a participant in channel: {identifier}")
                    logging.warning(f"ℹ️ [INFO] Already a participant in channel: {identifier}")
                except FloodWaitError as e:
                    logging.error(f"❌ [ERROR] Flood wait error. Sleeping for {e.seconds} seconds.")
                    await asyncio.sleep(e.seconds)
                except Exception as e:
                    # This could be due to various reasons, e.g., channel doesn't exist.
                    logging.error(f"❌ [ERROR] Failed to join channel {identifier}: {e}")

        except Exception as e:
            logging.error(f"An unexpected error occurred in the processing loop: {e}")
        
        await asyncio.sleep(5)