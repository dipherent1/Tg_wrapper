# src/app/core/bot.py

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import asyncio
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
)
from app.core.bot_utils import ensure_user # <-- Import our new decorator
from app.services.subscription_service import add_subscription_for_user

from app.config.config import settings
from app.services.join_request_service import create_join_request

# --- Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- State definitions for our Conversation ---
(ASK_CHANNEL, ASK_TAGS) = range(2)
(ASK_QUERY,) = range(1) # We only need one state for this conversation

# --- List of available tags. Later this can come from the DB. ---
# As requested, 'default' is included as a choice.
AVAILABLE_TAGS = ["default", "News", "Crypto", "Jobs", "Deals", "Tech", "Resources"]




# --- Conversation Step 1: Start the flow ---
@ensure_user
async def add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to add a new channel."""
    # The decorator has already saved the user to the DB and their ID to context.
    await update.message.reply_text(
        "Okay, let's add a new channel.\n\n"
        "Please forward a message, or send a public link/username.\n\n"
        "Send /cancel at any time to stop."
    )
    return ASK_CHANNEL




# --- Conversation Step 2: Handle ALL channel input types ---
async def handle_channel_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Parses any valid user input (forward, link, username) and asks for tags."""
    identifier = None
    display_name = "the channel"

    message = update.message
    
    # Case 1: Forwarded message (most reliable)
    if message.forward_origin and message.forward_origin.type == 'channel':
        origin_chat = message.forward_origin.chat
        # If public, use username. If private, the listener will need the ID.
        identifier = f"@{origin_chat.username}" if origin_chat.username else str(origin_chat.id)
        display_name = f"'{origin_chat.title}'"
    
    # Case 2: Text input (link or username)
    elif message.text:
        text = message.text.strip()
        if text.startswith('@') or 't.me/' in text:
            identifier = text
            display_name = text
        else:
            await message.reply_text("That doesn't look like a username or link or forwarded from a channel. Please try again.")
            return ASK_CHANNEL

    if not identifier:
        await message.reply_text("I couldn't recognize that. Please forward a message, or send a username/link.")
        return ASK_CHANNEL

    # We have a valid identifier! Store it and proceed to tag selection.
    context.user_data['identifier'] = identifier
    context.user_data['display_name'] = display_name
    context.user_data['selected_tags'] = set()

    # --- Create keyboard for tag selection (code is identical to before) ---
    keyboard_buttons = [InlineKeyboardButton(tag, callback_data=f"tag_{tag}") for tag in AVAILABLE_TAGS]
    keyboard = [keyboard_buttons[i:i + 3] for i in range(0, len(keyboard_buttons), 3)]
    keyboard.append([InlineKeyboardButton("✅ Done", callback_data="tags_done")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await message.reply_text(
        f"Great, I've got {display_name}. Now, let's add some tags.",
        reply_markup=reply_markup
    )
    
    return ASK_TAGS


# --- Conversation Step 3: Handle Tag Selection & Create Join Request ---
# --- Conversation Step 3: Handle Tag Selection (NOW USES THE USER ID FROM CONTEXT) ---
async def handle_tag_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if query.data == "tags_done":
        identifier = context.user_data['identifier']
        display_name = context.user_data['display_name']
        selected_tags = list(context.user_data.get('selected_tags', set()))
        if not selected_tags:
            selected_tags.append("default")

        try:
            # --- THE FIX ---
            # The user's DB ID was saved to the context by the @ensure_user decorator.
            db_user_id = context.user_data['db_user_id']
            if not db_user_id:
                raise ValueError("User could not be found or created.")

            # Call the service, which now only needs the ID
            create_join_request(
                identifier=identifier,
                tags=selected_tags,
                user_id=db_user_id # Pass the UUID directly
            )
            
            final_tags_str = ', '.join(selected_tags)
            await query.edit_message_text(
                f"Request received! I've added {display_name} to my queue with tags: {final_tags_str}.\n"
                "I will try to join it and will let you know if I succeed."
            )
        except Exception as e:
            logger.error(f"Error creating join request from bot: {e}", exc_info=True)
            await query.edit_message_text("Sorry, an internal error occurred. Please try again later.")
            
        context.user_data.clear()
        return ConversationHandler.END

    # ... The rest of the tag selection logic (toggling buttons) remains the same ...
    elif query.data.startswith("tag_"):
        tag = query.data.split("_", 1)[1]
        selected_tags = context.user_data.get('selected_tags', set())
        if tag in selected_tags: selected_tags.remove(tag)
        else: selected_tags.add(tag)
        
        keyboard_buttons = [InlineKeyboardButton(f"✅ {t}" if t in selected_tags else t, callback_data=f"tag_{t}") for t in AVAILABLE_TAGS]
        keyboard = [keyboard_buttons[i:i + 3] for i in range(0, len(keyboard_buttons), 3)]
        keyboard.append([InlineKeyboardButton("✅ Done", callback_data="tags_done")])
        
        await query.edit_message_reply_markup(reply_markup=InlineKeyboardMarkup(keyboard))
        return ASK_TAGS


@ensure_user # Use the decorator to make sure the user exists in our DB
async def subscribe_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the /subscribe conversation."""
    await update.message.reply_text(
        "Let's create a new alert.\n\n"
        "What text are you looking for? (e.g., 'remote python job', 'macbook under 50000 birr', etc.)\n\n"
        "Send /cancel to stop."
    )
    return ASK_QUERY

async def handle_query_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the user's query text and saves the subscription."""
    query_text = update.message.text
    if not query_text or len(query_text) < 3:
        await update.message.reply_text("That query is too short. Please provide a more descriptive search term.")
        return ASK_QUERY # Ask again

    try:
        # The @ensure_user decorator already put the user's DB ID in the context
        db_user_id = context.user_data.get('db_user_id')
        if not db_user_id:
            raise ValueError("Could not find user in context. Please /start the bot again.")

        # Call our clean, reusable service function
        add_subscription_for_user(
            user_id=db_user_id,
            query_text=query_text
        )

        await update.message.reply_text(
            f"✅ Subscription created! I will now notify you whenever I see messages containing: '{query_text}'"
        )
        return ConversationHandler.END # End the conversation successfully

    except Exception as e:
        logger.error(f"Error creating subscription: {e}", exc_info=True)
        await update.message.reply_text("Sorry, an internal error occurred. Your subscription was not created.")
        return ConversationHandler.END

async def subscribe_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the subscribe conversation."""
    await update.message.reply_text("Okay, I've cancelled the subscription process.")
    return ConversationHandler.END
# --- Conversation Fallback: Cancel ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation, clearing any stored data."""
    await update.message.reply_text("Okay, I've cancelled the process.")
    context.user_data.clear()
    return ConversationHandler.END


# src/app/core/bot.py

# ... (all your imports and handler functions are correct) ...


# --- Main Bot Setup (Synchronous and Simple) ---
def main() -> None:
    """Sets up and runs the bot with all handlers."""
    
    # 1. Create the Application object
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # 2. Add all your handlers

    # Subscription Conversation Handler
    subscribe_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("subscribe", subscribe_start)],
        states={
            ASK_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_query_input)],
        },
        fallbacks=[CommandHandler("cancel", subscribe_cancel)],
        # It's good practice to allow conversations to time out
        conversation_timeout=600 # 10 minutes
    )
    application.add_handler(subscribe_conv_handler)
    
    # Channel Conversation Handler
    add_channel_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("addchannel", add_channel_start)],
        states={
            ASK_CHANNEL: [MessageHandler(filters.TEXT | filters.FORWARDED, handle_channel_input)],
            ASK_TAGS: [
                CallbackQueryHandler(handle_tag_selection, pattern="^tags_done$"),
                CallbackQueryHandler(handle_tag_selection, pattern="^tag_")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        conversation_timeout=600 # 10 minutes
    )
    application.add_handler(add_channel_conv_handler)

    # Start Command
    @ensure_user
    async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Welcome! Use /addchannel or /subscribe.")
    application.add_handler(CommandHandler("start", start_cmd))

    logger.info("[Bot] Starting polling...")
    
    # 3. Run the bot until you press Ctrl-C
    # This method is blocking and handles the asyncio loop internally for you.
    # It takes care of initialization, running, and shutdown automatically.
    application.run_polling()


if __name__ == "__main__":
    # No asyncio.run() needed, just call the synchronous main function.
    main()