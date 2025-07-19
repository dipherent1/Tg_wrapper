# src/app/main.py

import asyncio
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.config.config import settings
from app.core.telethon_client import get_telethon_client, ACTIVE_CLIENTS
from app.core.event_handler import setup_event_handlers
from app.core.background_tasks import process_join_requests_task # <-- Renamed for clarity

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("--- Starting application lifespan ---")
    
    # We only need one client instance for both listening and joining
    main_session_name = "bini"
    client = get_telethon_client(main_session_name)
    
    logger.info(f"Connecting main client for '{main_session_name}'...")
    await client.start()
    
    # 1. Setup the new message listener
    setup_event_handlers(client)
    
    # 2. Start the background task for processing join requests
    asyncio.create_task(process_join_requests_task(client))
    
    ACTIVE_CLIENTS[main_session_name] = client
    logger.info(f"[SUCCESS] Client is running. Listening for messages and processing join requests.")
    
    yield
    
    logger.info("--- Shutting down application lifespan ---")
    if client.is_connected():
        await client.disconnect()
        logger.info(f"Client for '{main_session_name}' disconnected.")

# Create the FastAPI app with the lifespan manager
app = FastAPI(lifespan=lifespan)

# ... (rest of your main.py file is fine) ...
# app.include_router(onboarding.router, prefix="/api", tags=["Onboarding"])

@app.get("/")
def read_root():
    return {"status": "Telegram Notifier API is running", "active_clients": list(ACTIVE_CLIENTS.keys())}