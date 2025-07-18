# src/app/core/bot.py

import logging
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    CallbackQueryHandler,
    filters,
)

from app.config.config import settings

# --- Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
JOIN_QUEUE_FILE = "join_queue.txt"

# --- State definitions for our Conversation ---
(ASK_CHANNEL, ASK_TAGS) = range(2)

# --- (Temporary) List of tags. Later this will come from the DB. ---
AVAILABLE_TAGS = ["News", "Crypto", "Jobs", "Deals", "Tech"]


# --- Conversation Step 1: Start the flow ---
async def add_channel_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Starts the conversation to add a new channel."""
    await update.message.reply_text(
        "Okay, let's add a new channel.\n\n"
        "Please send me the channel's public username (e.g., @duolingo), "
        "its t.me link, or an invite link for a private channel.\n\n"
        "You can also just forward a message from the channel.\n\n"
        "Send /cancel at any time to stop."
    )
    return ASK_CHANNEL


# --- Conversation Step 2: Handle the user's channel input ---
async def handle_channel_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Parses the user's input to identify the channel and asks for tags."""
    identifier = None
    channel_title = "the channel" # Default title

    # Case 1: User forwarded a message
    if update.message.forward_origin and update.message.forward_origin.type == 'channel':
        origin_chat = update.message.forward_origin.chat
        channel_title = f"'{origin_chat.title}'"
        if origin_chat.username:
            identifier = f"@{origin_chat.username}"
        else: # Private channel forward
            await update.message.reply_text("Forwarding from a private channel doesn't give me an invite link. Please send the `t.me/+...` link directly.")
            return ASK_CHANNEL # Ask again

    # Case 2: User sent text (username, url, or invite link)
    elif update.message.text:
        text = update.message.text
        if text.startswith('@'):
            identifier = text
        elif 't.me/' in text or 'telegram.me/' in text:
            # Basic validation for links
            if 'joinchat' in text or '+' in text or re.search(r't\.me/([a-zA-Z0-9_]{5,})', text):
                 identifier = text
            else:
                 await update.message.reply_text("That doesn't look like a valid channel link. Please try again.")
                 return ASK_CHANNEL

    if not identifier:
        await update.message.reply_text("I couldn't recognize that. Please send a username, a valid link, or forward a message.")
        return ASK_CHANNEL

    # We have a valid identifier, save it and move to the next step
    context.user_data['channel_identifier'] = identifier
    context.user_data['selected_tags'] = set()

    # Create buttons for tags
    keyboard = [
        [InlineKeyboardButton(tag, callback_data=f"tag_{tag}") for tag in AVAILABLE_TAGS],
        [InlineKeyboardButton("✅ Done", callback_data="tags_done")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"Great, I've got {channel_title}. Now, let's add some tags. "
        "Select all that apply, then press 'Done'.",
        reply_markup=reply_markup
    )
    return ASK_TAGS


# --- Conversation Step 3: Handle Tag Selection ---
async def handle_tag_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles the user pressing tag buttons."""
    query = update.callback_query
    await query.answer() # Acknowledge the button press

    callback_data = query.data

    if callback_data == "tags_done":
        # Final step: Save to queue and end conversation
        identifier = context.user_data['channel_identifier']
        tags = context.user_data.get('selected_tags', set())
        
        # Write to the queue file: identifier,tag1,tag2,...
        queue_line = f"{identifier},{','.join(tags)}\n"
        with open(JOIN_QUEUE_FILE, "a") as f:
            f.write(queue_line)

        await query.edit_message_text(f"All set! I will try to join and monitor the channel with tags: {', '.join(tags) or 'None'}.")
        context.user_data.clear()
        return ConversationHandler.END

    elif callback_data.startswith("tag_"):
        tag = callback_data.split("_")[1]
        selected_tags = context.user_data.get('selected_tags', set())

        # Toggle selection
        if tag in selected_tags:
            selected_tags.remove(tag)
        else:
            selected_tags.add(tag)
        
        # Update the buttons to show selection
        keyboard = []
        for t in AVAILABLE_TAGS:
            text = f"✅ {t}" if t in selected_tags else t
            keyboard.append(InlineKeyboardButton(text, callback_data=f"tag_{t}"))
        
        # Recreate keyboard in rows of 3
        final_keyboard = [keyboard[i:i + 3] for i in range(0, len(keyboard), 3)]
        final_keyboard.append([InlineKeyboardButton("✅ Done", callback_data="tags_done")])
        reply_markup = InlineKeyboardMarkup(final_keyboard)
        
        await query.edit_message_reply_markup(reply_markup=reply_markup)
        return ASK_TAGS


# --- Conversation Fallback: Cancel ---
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    await update.message.reply_text("Okay, I've cancelled the process.")
    context.user_data.clear()
    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    application = Application.builder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # Build the conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("addchannel", add_channel_start)],
        states={
            ASK_CHANNEL: [MessageHandler(filters.TEXT | filters.FORWARDED, handle_channel_input)],
            ASK_TAGS: [CallbackQueryHandler(handle_tag_selection)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_handler)
    
    # A simple start command for new users
    async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("Welcome! Use /addchannel to get started.")
    application.add_handler(CommandHandler("start", start_cmd))

    logging.info("[Bot] Starting polling...")
    application.run_polling()


if __name__ == "__main__":
    main()