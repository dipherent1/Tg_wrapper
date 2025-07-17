import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# --- Project-specific imports ---
# We need to access our database session and user repository logic
from app.config.config import Settings
from app.config.db import SessionLocal
from app.repo.user_repo import UserRepo
from app.domain.schemas import UserCreate

BOT_TOKEN = Settings().BOT_TOKEN
if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not found in .env file!")

# --- Bot Command Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /start command.
    Greets the user and saves their info to the database.
    """
    telegram_user = update.message.from_user

    # Data to be saved, conforming to our Pydantic schema
    user_data = UserCreate(
        telegram_user_id=telegram_user.id,
        first_name=telegram_user.first_name,
        username=telegram_user.username
    )

    # --- Database Interaction ---
    # BEST PRACTICE: Manage session scope carefully in standalone scripts
    # db = SessionLocal()
    # try:
    #     repo = UserRepo(db)
    #     db_user = repo.get_or_create_user(user_data)
    # finally:
    #     db.close()

    # Send a welcome message
    await update.message.reply_html(
        rf"Hi {telegram_user.mention_html()}! Welcome to Info-Stream."
        "\n\nI will help you find the information you care about from Telegram channels."
        "\n\nUse /subscribe to create a new alert."
    )


# --- Main function to run the bot ---
def main() -> None:
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    # Register the /start command handler
    application.add_handler(CommandHandler("start", start))

    # Add other handlers here later (e.g., for /subscribe)

    # Start the Bot
    application.run_polling()


if __name__ == '__main__':
    main()