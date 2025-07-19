# src/app/core/worker.py

import logging
from telethon import events

from app.repo.unit_of_work import UnitOfWork
from app.domain import schemas
from .notifier import send_telegram_notification

logger = logging.getLogger(__name__)

async def process_new_message(event: events.NewMessage.Event):
    """
    This is the core "worker" function for processing a single new message.
    It saves the message, runs the matching engine, and sends notifications.
    """
    try:
        message_text = event.raw_text
        if not message_text:
            return

        db_message = None
        with UnitOfWork() as uow:
            # Step 1: Save the message to our database.
            message_data = schemas.MessageCreate(
                telegram_message_id=event.message.id,
                channel_telegram_id=event.chat_id,
                content=message_text,
                sent_at=event.message.date,
            )
            db_message = uow.messages.create_message(message_data)
            
            if not db_message:
                logger.warning(f"Could not save message from channel {event.chat_id}, channel may not be in DB yet.")
                return

            # Step 2: Fetch all active subscriptions.
            active_subscriptions = uow.subscriptions.get_all_active_subscriptions()

        # --- Matching Engine (V1 - Keywords) ---
        if not active_subscriptions:
            return

        logger.info(f"Matching message from '{db_message.channel.name}' against {len(active_subscriptions)} subscriptions.")
        
        notified_users = set()
        for sub in active_subscriptions:
            if sub.user.telegram_id in notified_users:
                continue

            keywords = sub.query_text.lower().split()
            message_lower = message_text.lower()
            
            if any(keyword in message_lower for keyword in keywords):
                logger.info(f"MATCH FOUND! User: {sub.user.telegram_id}, Keyword: {sub.query_text}")
                
                # --- Step 3: Send Notification ---
                notification_text = (
                    f"🔥 <b>New Match Found!</b>\n\n"
                    f"<b>Channel:</b> {db_message.channel.name}\n"
                    f"<b>Subscription:</b> '{sub.query_text}'\n\n"
                    f"<blockquote>{message_text[:500]}</blockquote>\n"
                    f"<a href='{db_message.clickable_link}'>Go to Message</a>"
                )
                
                await send_telegram_notification(
                    user_telegram_id=sub.user.telegram_id,
                    message=notification_text
                )
                notified_users.add(sub.user.telegram_id)

    except Exception as e:
        logger.error(f"Error in process_new_message: {e}", exc_info=True)