# src/app/core/bot.py

import logging
from turtle import update
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import asyncio
from logging.handlers import RotatingFileHandler
import uuid
from app.services.subscription_service import add_subscription_for_user, get_user_subscriptions, cancel_subscription, edit_subscription
from app.services.tag_service import get_all_tags
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
)
from app.core.bot.bot_utils import ensure_user, escape_markdown_v2, normalize_identifier # <-- Import our new decorator
from app.services.user_service import get_or_create_user
import sentry_sdk

from app.config.config import settings, setup_logging_directory, setup_sessions_directory
from app.services.join_request_service import create_join_request

setup_logging_directory()  # Ensure logging directory exists
setup_sessions_directory()  # Ensure sessions directory exists

LOGS_DIR = settings.LOGS_DIR

logger = logging.getLogger("Bot") # Give it a custom name
logger.setLevel(logging.INFO)

# Create a dedicated file handler for the bot

log_file_path = LOGS_DIR / "bot.log"
bot_file_handler = RotatingFileHandler(log_file_path, maxBytes=5*1024*1024, backupCount=5)
bot_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

# Add the file handler to our bot logger
logger.addHandler(bot_file_handler)

# Also add a console handler to see logs in the terminal
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(console_handler)


if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=1.0
    )
    logging.info("Sentry monitoring is enabled for the bot.")
else:
    logging.warning("SENTRY_DSN not found. Sentry monitoring for the bot is disabled.")

# --- State definitions for our Conversation ---
(ASK_CHANNEL, ASK_TAGS) = range(2)
(ASK_QUERY,) = range(1) # We only need one state for this conversation
(ASK_NEW_QUERY,) = range(10, 11)

# --- List of available tags. Later this can come from the DB. ---
# As requested, 'others' is included as a choice.
AVAILABLE_TAGS = get_all_tags()
logger.info(f"Loaded {AVAILABLE_TAGS} available tags from the service.")




# --- Conversation Step 1: Start the flow ---
@ensure_user
async def add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to add a new channel."""
    # The decorator has already saved the user to the DB and their ID to context.
    await update.message.reply_text(
        "Let's add a new channel for monitoring!\n\n"
        "You can:\n"
        "• Forward a message from the channel\n"
        "• Send the channel's @username\n"
        "• Paste an invite link\n\n"
        "Type /cancel anytime to exit."
    )
    return ASK_CHANNEL




# --- Conversation Step 2: Handle ALL channel input types ---
async def handle_channel_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message
    user_input = ""

    if message.forward_origin and message.forward_origin.type == 'channel':
        origin_chat = message.forward_origin.chat
        user_input = f"@{origin_chat.username}" if origin_chat.username else str(origin_chat.id)
    elif message.text:
        user_input = message.text

    # --- NORMALIZE THE INPUT ---
    normalized_identifier = normalize_identifier(user_input)

    if not normalized_identifier:
        await message.reply_text("I couldn't recognize that format. Please send a valid username, link, or forward a message from a public channel/supergroups.")
        return ASK_CHANNEL

    # Store the NORMALIZED identifier and proceed to tag selection
    context.user_data['identifier'] = normalized_identifier

    context.user_data['display_name'] = normalized_identifier
    context.user_data['selected_tags'] = set()

    # --- Create keyboard for tag selection (code is identical to before) ---
    keyboard_buttons = [
        InlineKeyboardButton(tag.name, callback_data=f"tag_{tag.name}")
        for tag in AVAILABLE_TAGS
    ]
    
    keyboard = [keyboard_buttons[i:i + 3] for i in range(0, len(keyboard_buttons), 3)]
    keyboard.append([InlineKeyboardButton("✅ Done", callback_data="tags_done")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    channel_identifier = normalized_identifier if normalized_identifier.startswith('@') else f"the channel"
    await message.reply_text(
        f"Great, I've got {channel_identifier}. Now, let's add some tags.",
        reply_markup=reply_markup
    )
    
    return ASK_TAGS


# --- Conversation Step 3: Handle Tag Selection & Create Join Request ---
# --- Conversation Step 3: Handle Tag Selection (NOW USES THE USER ID FROM CONTEXT) ---
async def handle_tag_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processes button clicks for tag selection or finalizes the process."""
    query = update.callback_query
    await query.answer()

    callback_data = query.data

    if callback_data == "tags_done":
        # --- Finalize the process ---
        normalized_identifier = context.user_data['identifier']
        # The selected_tags set now contains slugs, e.g., {'backend-dev', 'jobs-hiring'}
        selected_tags = list(context.user_data.get('selected_tags', set()))

        # If no tags were selected, use the slug for the others tag.
        # We find the others tag's data from our loaded config.
        if not selected_tags:
            default_tag_slug = "others" # Fallback to 'others'
            selected_tags.append(default_tag_slug)
        
        try:
            db_user = get_or_create_user(query.from_user)
            
            # Call the service, passing the list of clean slugs
            join_req, was_newly_created = create_join_request(
                identifier=normalized_identifier,
                tags=selected_tags,
                user_id=db_user.id
            )

            # For the final message, we need to convert back to pretty names
            final_tag_names = [
                tag.name for tag in AVAILABLE_TAGS if tag.name in selected_tags
            ]
            final_tags_str = ', '.join(final_tag_names)
            
            if was_newly_created:
                await query.edit_message_text(
                    f"Request received! I've added '{normalized_identifier}' to my queue with tags: {final_tags_str}."
                )
            else:
                await query.edit_message_text(
                    f"This channel ('{normalized_identifier}') is already in the queue. No new request was created."
                )
        except Exception as e:
            logger.error(f"Error creating join request from bot: {e}", exc_info=True)
            await query.edit_message_text("Sorry, an internal error occurred. Please try again later.")
            
        context.user_data.clear()
        return ConversationHandler.END

    # --- THIS IS THE CORRECTED LOGIC FOR HANDLING TAG CLICKS ---
    elif callback_data.startswith("tag_"):
        # 1. Get the SLUG from the callback data
        tag_slug = callback_data.split("_", 1)[1]
        
        # 2. Get the set of selected SLUGS from the context
        selected_tags = context.user_data.get('selected_tags', set())

        # 3. Toggle the SLUG in the set
        if tag_slug in selected_tags:
            selected_tags.remove(tag_slug)
        else:
            selected_tags.add(tag_slug)
        
        # 4. Redraw the keyboard, iterating over the list of tag DICTIONARIES
        keyboard_buttons = []
        for tag in AVAILABLE_TAGS:
            slug = tag.name
            name = tag.name
            # Check if the SLUG is in our selected set
            text = f"✅ {name}" if slug in selected_tags else name
            # The button text is the NAME, the callback data is the SLUG
            keyboard_buttons.append(InlineKeyboardButton(text, callback_data=f"tag_{slug}"))
            
        # 5. Rebuild the keyboard layout
        keyboard = [keyboard_buttons[i:i + 3] for i in range(0, len(keyboard_buttons), 3)]
        keyboard.append([InlineKeyboardButton("✅ Done", callback_data="tags_done")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # 6. Edit the message with the updated keyboard
        await query.edit_message_reply_markup(reply_markup=reply_markup)
        
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

        tag_names = ["others"]
        add_subscription_for_user(
            user_id=db_user_id,
            query_text=query_text,
            tag_names=tag_names
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


@ensure_user
async def list_subscriptions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays a list of the user's active subscriptions with cancel buttons."""
    db_user_id = context.user_data.get('db_user_id')
    if not db_user_id:
        await update.message.reply_text("Could not find your profile. Please try /start first.")
        return

    # Call the service to get the subscriptions
    subscriptions = get_user_subscriptions(user_id=db_user_id)

    if not subscriptions:
        await update.message.reply_text("You have no active subscriptions. Use /subscribe to create one.")
        return

    message_text = "Here are your active subscriptions:\n"
    keyboard = []
    for sub in subscriptions: # 'sub' is now a schemas.Subscription object
        # The code below works without changes because the Pydantic model
        # has the same .query_text and .id attributes.
        query_preview = (sub.query_text[:30] + '...') if len(sub.query_text) > 30 else sub.query_text
        # --- THIS IS THE FIX ---
        # Escape any special characters in the user-generated content
        # escaped_preview = escape_markdown_v2(query_preview)
        
        # Now, construct the line using the *escaped* text.
        # We also need to escape the '-' for the list item itself.
        # message_text += f"\n\\- `{escaped_preview}`"
        
        # The button text does not need escaping as it's not parsed.
        keyboard.append([
            InlineKeyboardButton(f"✏️ Edit '{query_preview}'", callback_data=f"edit_sub_{sub.id}"),
            InlineKeyboardButton("❌ Cancel sub", callback_data=f"cancel_sub_{sub.id}")
        ])

    # reply_markup = InlineKeyboardMarkup(keyboard)
    # The message is now safe to send with MarkdownV2
    await update.message.reply_text("Manage your subscriptions:", reply_markup=InlineKeyboardMarkup(keyboard))

async def edit_subscription_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the edit subscription conversation when an 'Edit' button is pressed."""
    query = update.callback_query
    await query.answer()

    # Store the subscription ID we want to edit in the context
    sub_id_str = query.data.replace("edit_sub_", "")
    context.user_data['subscription_to_edit'] = sub_id_str

    await query.edit_message_text(
        text="Okay, please send me the new text for this alert.\n\nSend /cancel to stop editing."
    )
    return ASK_NEW_QUERY

async def handle_new_query_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the user's new query text and finalizes the edit."""
    new_query_text = update.message.text
    subscription_id_str = context.user_data.get('subscription_to_edit')

    try:
        subscription_id = uuid.UUID(subscription_id_str)
        
        # Get the user's DB ID
        db_user = get_or_create_user(update.effective_user)
        
        # Call the edit service
        success = edit_subscription(
            user_id=db_user.id,
            subscription_id=subscription_id,
            new_query_text=new_query_text
        )

        if success:
            await update.message.reply_text(f"✅ Subscription updated successfully to: '{new_query_text}'")
        else:
            await update.message.reply_text("Could not update subscription. The new text might be too short or an error occurred.")

    except (ValueError, TypeError):
        await update.message.reply_text("Error: Invalid subscription format.")
    except Exception as e:
        logger.error(f"Error handling new query input: {e}", exc_info=True)
        await update.message.reply_text("An internal error occurred.")
    
    context.user_data.clear()
    return ConversationHandler.END


async def edit_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels the edit subscription conversation."""
    await update.message.reply_text("Okay, edit cancelled.")
    context.user_data.clear()
    return ConversationHandler.END



async def handle_cancel_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the 'Cancel' button press by calling the appropriate services."""
    query = update.callback_query
    await query.answer()

    try:
        sub_id_str = query.data.replace("cancel_sub_", "")
        subscription_id = uuid.UUID(sub_id_str)
        
        # --- THIS IS THE CORRECTED LOGIC ---
        # 1. Call the user service to get the user's DB info
        db_user = get_or_create_user(query.from_user)

        # 2. Call the subscription service with the necessary IDs
        success = cancel_subscription(
            user_id=db_user.id, 
            subscription_id=subscription_id
        )

        if success:
            await query.edit_message_text("✅ Subscription successfully cancelled.")
        else:
            await query.edit_message_text("Could not cancel subscription. It may have already been removed.")

    except (ValueError, TypeError):
        await query.edit_message_text("Error: Invalid subscription format.")
    except Exception as e:
        logger.error(f"Error handling cancel button: {e}", exc_info=True)
        await query.edit_message_text("An internal error occurred.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays a helpful message with all available commands."""
    
    # Using HTML for better formatting (bold tags)
    help_text = (
        "<b>Welcome to Info-Stream!</b>\n\n"
        "I am your personal search and alert engine for Telegram. "
        "I monitor channels and notify you when messages match your interests.\n\n"
        "<b>Available Commands:</b>\n\n"
        "▶️  /start - Register with the bot.\n\n"
        "➕  /addchannel - Start a conversation to add a new channel for monitoring. I'll ask you for the channel's link/username and some tags.\n\n"
        "🔔  /subscribe - Create a new alert. I'll ask you what text you're looking for.\n\n"
        "📋  /mysubscriptions - List all your active alerts with options to cancel them.\n\n"
        "❓  /help - Show this help message."
    )
    
    await update.message.reply_text(help_text, parse_mode='HTML')
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
        conversation_timeout=600, # 10 minutes
    )
    application.add_handler(subscribe_conv_handler)
    application.add_handler(CommandHandler("mysubscriptions", list_subscriptions))
    application.add_handler(CallbackQueryHandler(handle_cancel_button, pattern="^cancel_sub_"))
    application.add_handler(CommandHandler("help", help_command))

    
    edit_sub_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_subscription_start, pattern="^edit_sub_")],
        states={
            ASK_NEW_QUERY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_query_input)],
        },
        fallbacks=[CommandHandler("cancel", edit_cancel)],
        # This allows the handler to be triggered by a button from another handler
        map_to_parent={
            ConversationHandler.END: -1 # Or another state if you want to go back to the list
        },
        conversation_timeout=600,# 10 minutes
    )
    application.add_handler(edit_sub_conv_handler)

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
        conversation_timeout=600,# 10 minutes
    )
    application.add_handler(add_channel_conv_handler)

    # Start Command
    @ensure_user
    async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Welcome! Use /help or more.")
    application.add_handler(CommandHandler("start", start_cmd))

    logger.info("[Bot] Starting polling...")

    # 3. Run the bot until you press Ctrl-C
    # This method is blocking and handles the asyncio loop internally for you.
    # It takes care of initialization, running, and shutdown automatically.
    application.run_polling()


if __name__ == "__main__":
    # No asyncio.run() needed, just call the synchronous main function.
    main()