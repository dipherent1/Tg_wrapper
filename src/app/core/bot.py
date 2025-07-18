# src/app/core/bot.py

import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from app.config.config import settings

JOIN_QUEUE_FILE = "join_queue.txt"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # ... (start function is the same) ...
    telegram_user = update.effective_user
    await update.message.reply_html(
        rf"Hi {telegram_user.mention_html()}! Welcome to Info-Stream."
        "\n\nForward a message from a public channel you want me to monitor."
    )

async def handle_forwarded_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles forwarded messages. If from a public channel, adds its username
    to the queue file. If private, informs the user about the limitation.
    """
    origin = update.message.forward_origin
    if not origin or origin.type != 'channel':
        await update.message.reply_text("Please forward a message from a channel or a group.")
        return

    # The Chat object contains the channel's details
    channel_chat = origin.chat
    
    # --- THIS IS THE KEY LOGIC ---
    if channel_chat.username:
        # This is a public channel, we have a username!
        channel_identifier = f"@{channel_chat.username}"
        
        try:
            with open(JOIN_QUEUE_FILE, "a") as f:
                f.write(f"{channel_identifier}\n")
            
            logging.info(f"[Bot] Added public channel '{channel_identifier}' to queue.")
            await update.message.reply_text(
                f"Thanks! Added public channel '{channel_chat.title}' to my queue. I'll join it shortly."
            )
        except Exception as e:
            logging.error(f"[Bot] Error writing to queue file: {e}")
            await update.message.reply_text("Sorry, an internal error occurred.")
            
    else:
        # This is a private channel, it has no username.
        logging.warning(f"[Bot] User tried to add private channel '{channel_chat.title}' (ID: {channel_chat.id}).")
        await update.message.reply_text(
            f"Sorry, I can't automatically join private channels like '{channel_chat.title}'. "
            "I can only join public channels that have a username (e.g., @channel_name)."
        )

def main() -> None:
    # ... (main function is the same) ...
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    application = Application.builder().token(settings.BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.FORWARDED, handle_forwarded_message))
    logging.info("[Bot] Starting polling...")
    application.run_polling()

if __name__ == '__main__':
    main()