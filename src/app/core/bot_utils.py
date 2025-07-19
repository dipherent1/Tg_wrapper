# src/app/core/bot_utils.py

import logging
from functools import wraps
from telegram import Update
from telegram.ext import ContextTypes
from app.repo.unit_of_work import UnitOfWork
from app.domain import schemas

logger = logging.getLogger(__name__)

def ensure_user(func):
    """
    A decorator that ensures the user sending a command/message is present in the database.
    It performs a "get or create" operation and handles potential errors.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not update.effective_user:
            return

        # --- THIS IS THE NEW ERROR HANDLING BLOCK ---
        try:
            user_data = schemas.UserCreate(
                telegram_id=update.effective_user.id,
                full_name=update.effective_user.full_name,
                username=update.effective_user.username,
            )

            with UnitOfWork() as uow:
                db_user = uow.users.get_or_create_user(user_data)
                context.user_data['db_user_id'] = db_user.id
                context.user_data['db_user_status'] = db_user.status
            
            # If everything succeeded, run the original command function
            return await func(update, context, *args, **kwargs)

        except Exception as e:
            # If ANYTHING goes wrong (like the DB error we just saw), log it and tell the user.
            logger.error(
                f"Error in @ensure_user for user {update.effective_user.id}: {e}", 
                exc_info=True # Include the full traceback in the logs
            )
            await update.message.reply_text(
                "Sorry, a critical error occurred while accessing your profile. "
                "The administrators have been notified. Please try again later."
            )
            # We don't continue to the wrapped function if there was an error
            return

    return wrapper