# src/app/services/matching_service.py

import logging
from app.repo.unit_of_work import UnitOfWork
from app.domain import schemas
from app.core.bot.notifier import send_telegram_notification
from app.core.ai.ai_engine import generate_embedding
# We no longer need numpy or scipy here, the DB does the math!

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.7 # Tune this for Gemini's embeddings

def create_clickable_link(channel_telegram_id, telegram_message_id) -> str:
    """
    Generates a clickable t.me link for a message.
    This helper is kept here as per the design decision.
    """
    if channel_telegram_id < -1_000_000_000_000:
        simple_channel_id = abs(channel_telegram_id) - 1_000_000_000_000
        return f"https://t.me/c/{simple_channel_id}/{telegram_message_id}"
    else:
        return f"https://t.me/c/{abs(channel_telegram_id)}/{telegram_message_id}"


# --- THE REFACTORED FUNCTION ---
async def run_matching_for_message(message_schema: schemas.MessageCreate, channel_data: schemas.ChannelCreate):
    """
    The dedicated AI matching engine. It operates in real-time on incoming message
    data and leverages the database for efficient vector search.
    """
    if not message_schema.content:
        return

    logger.info(f"Matcher: Processing message from '{channel_data.name}': '{message_schema.content[:50]}...'")
    
    try:
        # Step 1: Generate embedding for the new message (as a "document" to be searched).
        message_embedding = generate_embedding(message_schema.content, task_type="RETRIEVAL_DOCUMENT")

        if not message_embedding:
            logger.warning("Could not generate embedding for message. Skipping match.")
            return

        # Step 2: Use the repository to find potential matches directly in the DB.
        # This is now one single, efficient database call.
        with UnitOfWork() as uow:
            matching_subs_orm = uow.subscriptions.find_similar_subscriptions(
                message_embedding=message_embedding,
                threshold=SIMILARITY_THRESHOLD
            )
            # Convert to Pydantic schemas to safely use them outside the session.
            matching_subs = [schemas.Subscription.model_validate(sub) for sub in matching_subs_orm]

        if not matching_subs:
            logger.info(f"No subscriptions found above threshold for this message.")
            return

        # Step 3: Send notifications for the matches found by the database.
        notified_user_ids = set()
        for sub in matching_subs:
            if sub.user.telegram_id in notified_user_ids:
                continue

            logger.info(f"AI MATCH FOUND! User: {sub.user.telegram_id}, Sub: '{sub.query_text}'")
            
            # Use your helper function as requested
            redirect_link = create_clickable_link(
                channel_telegram_id=channel_data.telegram_id,
                telegram_message_id=message_schema.telegram_message_id
            )
            
            notification_text = (
                f"🔥 <b>New AI Match Found!</b>\n\n"
                f"<b>Channel:</b> {channel_data.name}\n"
                f"<b>Your Alert:</b> '{sub.query_text}'\n\n"
                f"<blockquote>{message_schema.content[:500]}</blockquote>\n"
                f"<a href='{redirect_link}'>Go to Message</a>"
            )
            
            await send_telegram_notification(
                user_telegram_id=sub.user.telegram_id,
                message=notification_text
            )
            notified_user_ids.add(sub.user.telegram_id)

    except Exception as e:
        logger.error(f"Critical error in matching engine: {e}", exc_info=True)