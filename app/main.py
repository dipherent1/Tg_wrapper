# app/main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
from .config import USER_SETTINGS
from .core.telethon_client import get_telethon_client, ACTIVE_CLIENTS
from .core.event_handler import setup_event_handlers
from .routers import onboarding

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Code to run on startup ---
    print("--- Starting background Telegram listeners... ---")
    for session_name, user_config in USER_SETTINGS.items():
        client = get_telethon_client(session_name)
        print(f"Initializing client for '{session_name}'...")
        
        # Connect and set up handlers
        await client.start()
        if not await client.is_user_authorized():
            print(f"[WARNING] Client for '{session_name}' is not authorized. Skipping.")
            continue
        
        setup_event_handlers(client, user_config)
        ACTIVE_CLIENTS[session_name] = client
        print(f"[SUCCESS] Client for '{session_name}' is running in the background.")
    
    yield # The application runs here

    # --- Code to run on shutdown ---
    print("--- Shutting down Telegram clients... ---")
    for session_name, client in ACTIVE_CLIENTS.items():
        if client.is_connected():
            await client.disconnect()
            print(f"Client for '{session_name}' disconnected.")


# Create the FastAPI app with the lifespan manager
app = FastAPI(lifespan=lifespan)

# Include the onboarding router
app.include_router(onboarding.router, prefix="/api", tags=["Onboarding"])

@app.get("/")
def read_root():
    return {"status": "Telegram Notifier API is running", "active_clients": list(ACTIVE_CLIENTS.keys())}