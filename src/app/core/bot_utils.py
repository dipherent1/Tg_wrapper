# src/app/core/bot_utils.py

import logging
from functools import wraps
import re
from telegram import Update
from telegram.ext import ContextTypes
# --- NEW: Import the service ---
from app.services.user_service import get_or_create_user

logger = logging.getLogger(__name__)

def ensure_user(func):
    """
    Decorator that calls the UserService to get/create a user and attaches
    their DB ID to the context.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not update.effective_user:
            return
        
        try:
            # --- Call the service ---
            db_user = get_or_create_user(update.effective_user)
            
            # Attach the user's UUID to the context
            context.user_data['db_user_id'] = db_user.id
            context.user_data['db_user_status'] = db_user.status
            
            return await func(update, context, *args, **kwargs)

        except Exception as e:
            logger.error(f"Error in @ensure_user for user {update.effective_user.id}: {e}", exc_info=True)
            await update.message.reply_text(
                "Sorry, a critical error occurred while accessing your profile. Please try again later."
            )
            return
    
    return wrapper

def escape_markdown_v2(text: str) -> str:
    """Escapes text for Telegram's MarkdownV2 parse mode."""
    # The characters to be escaped are: _ * [ ] ( ) ~ ` > # + - = | { } . !
    escape_chars = r'\_*[]()~`>#+-=|{}.!'
    # We use re.sub() to find any character from the list and prepend it with a '\'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)
