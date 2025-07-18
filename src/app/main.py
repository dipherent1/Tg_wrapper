# src/app/main.py

import sys
import os
import asyncio # <-- Add this import
from fastapi import FastAPI
from contextlib import asynccontextmanager

from .core.background_tasks import process_join_queue_task

from .core.telethon_client import get_telethon_client, ACTIVE_CLIENTS
from .core.event_handler import setup_event_handlers
from .routers import onboarding

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Code to run on startup ---
    print("--- Starting background Telegram listeners... ---")
    
    # We will assume the first user in the config is the one that joins channels
    # This is a simplification for now.
    main_session_name = "bini"
    
    client = get_telethon_client(main_session_name)
    print(f"Initializing main client for '{main_session_name}'...")
    
    await client.start()
    
    setup_event_handlers(client)
    ACTIVE_CLIENTS[main_session_name] = client
    print(f"[SUCCESS] Client for '{main_session_name}' is running.")
    
    # --- START THE BACKGROUND TASK ---
    print("--- Starting background join queue processor... ---")
    asyncio.create_task(process_join_queue_task(client))
    
    yield # The application runs here

    # --- Code to run on shutdown ---
    print("--- Shutting down Telegram clients... ---")
    for session_name, client in ACTIVE_CLIENTS.items():
        if client.is_connected():
            await client.disconnect()
            print(f"Client for '{session_name}' disconnected.")


# Create the FastAPI app with the lifespan manager
app = FastAPI(lifespan=lifespan)

# ... (rest of your main.py file is fine) ...
app.include_router(onboarding.router, prefix="/api", tags=["Onboarding"])

@app.get("/")
def read_root():
    return {"status": "Telegram Notifier API is running", "active_clients": list(ACTIVE_CLIENTS.keys())}