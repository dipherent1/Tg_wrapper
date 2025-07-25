# src/app/main.py

import asyncio
import logging
from re import L
from fastapi import FastAPI
from contextlib import asynccontextmanager
from logging.handlers import RotatingFileHandler # <-- Import for file logging
import sentry_sdk # <-- Import Sentry
from app.config.config import settings, setup_logging_directory, setup_sessions_directory
from app.core.listener.telethon_client import get_telethon_client, ACTIVE_CLIENTS
from app.core.listener.event_handler import setup_event_handlers
from app.core.listener.background_tasks import process_join_requests_task # <-- Renamed for clarity
from app.routers.routers import get_routers

setup_logging_directory()  # Ensure logging directory exists
setup_sessions_directory()  # Ensure sessions directory exists

LOGS_DIR = settings.LOGS_DIR
log_file_path = LOGS_DIR / "api_listener.log"

file_handler = RotatingFileHandler(log_file_path, maxBytes=5*1024*1024, backupCount=5)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Configure basic console logging and add the file handler
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(), # To see logs in the console
        file_handler           # To save logs to a file
    ]
)
logger = logging.getLogger(__name__)

# Initialize Sentry SDK if a DSN is provided
if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        # Enable performance monitoring
        traces_sample_rate=1.0,
        # Enable profiling
        profiles_sample_rate=1.0,
        # Add the FastAPI integration
    )
    logger.info("Sentry monitoring is enabled.")
else:
    logger.warning("SENTRY_DSN not found. Sentry monitoring is disabled.")

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

app.include_router(get_routers())
# ... (rest of your main.py file is fine) ...
# app.include_router(onboarding.router, prefix="/api", tags=["Onboarding"])

@app.get("/")
def read_root():
    return {"status": "Telegram Notifier API is running"}

@app.get("/sentry-debug")
async def trigger_error():
    division_by_zero = 1 / 0