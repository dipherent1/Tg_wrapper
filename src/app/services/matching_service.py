# src/app/services/matching_service.py

import logging
from app.repo.unit_of_work import UnitOfWork
from app.domain import models, schemas
from app.core.bot.notifier import send_telegram_notification

logger = logging.getLogger(__name__)

async def run_matching_for_message(message_schema: schemas.Message, channel_data: schemas.ChannelCreate):
    """
    This is the dedicated matching engine. It takes a saved message
    and checks it against all active subscriptions.
    
    This function is designed to be the time/energy consuming part.
    """
    logger.info(f"Matcher: Running for message {message_schema.id} from '{channel_data.name}'")

    # We still need the UoW to fetch subscriptions.
    active_subscriptions: list[schemas.Subscription] = []
    with UnitOfWork() as uow:
        # The repo now eagerly loads the user data in one query
        subs_orm = uow.subscriptions.get_all_active_subscriptions()
        active_subscriptions = [schemas.Subscription.model_validate(sub) for sub in subs_orm]

    if not active_subscriptions:
        logger.info("Matcher: No active subscriptions. Nothing to do.")
        return

    # notified_users = set()
    for sub in active_subscriptions:
        
        # --- Matching Logic (V1 - Keywords) ---
        # In the future, this block will be replaced with a call to a semantic search model.
        is_match = False
        keywords = sub.query_text.lower().split()
        message_lower = message_schema.content.lower()
        if any(keyword in message_lower for keyword in keywords):
            is_match = True
        # --- End of Matching Logic ---

        if is_match:
            logger.info(f"MATCH FOUND! User: {sub.user.telegram_id}, Sub ID: {sub.id}, Msg ID: {message_schema.id}")
            
            notification_text = (
                f"🔥 <b>New Match Found!</b>\n\n"
                f"<b>Channel:</b> {channel_data.name}\n"
                f"<b>Subscription:</b> '{sub.query_text}'\n\n"
                f"<blockquote>{message_schema.content[:500]}</blockquote>\n"
                f"<a href='{message_schema.clickable_link}'>Go to Message</a>"
            )
            
            await send_telegram_notification(
                user_telegram_id=sub.user.telegram_id,
                message=notification_text
            )