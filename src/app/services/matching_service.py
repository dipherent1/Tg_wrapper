# src/app/services/matching_service.py

import logging
from app.repo.unit_of_work import UnitOfWork
from app.domain import models, schemas
from app.core.bot.notifier import send_telegram_notification
from app.core.ai.ai_engine import generate_embedding
from scipy.spatial.distance import cosine # For fast calculation
import numpy as np


logger = logging.getLogger(__name__)

# async def run_matching_for_message(message_schema: schemas.Message, channel_data: schemas.ChannelCreate):
#     """
#     This is the dedicated matching engine. It takes a saved message
#     and checks it against all active subscriptions.
    
#     This function is designed to be the time/energy consuming part.
#     """
#     logger.info(f"Matcher: Running for message {message_schema.id} from '{channel_data.name}'")

#     # We still need the UoW to fetch subscriptions.
#     active_subscriptions: list[schemas.Subscription] = []
#     with UnitOfWork() as uow:
#         # The repo now eagerly loads the user data in one query
#         subs_orm = uow.subscriptions.get_all_active_subscriptions()
#         active_subscriptions = [schemas.Subscription.model_validate(sub) for sub in subs_orm]

#     if not active_subscriptions:
#         logger.info("Matcher: No active subscriptions. Nothing to do.")
#         return

#     # notified_users = set()
#     for sub in active_subscriptions:
        
#         # --- Matching Logic (V1 - Keywords) ---
#         # In the future, this block will be replaced with a call to a semantic search model.
#         is_match = False
#         keywords = sub.query_text.lower().split()
#         message_lower = message_schema.content.lower()
#         if any(keyword in message_lower for keyword in keywords):
#             is_match = True
#         # --- End of Matching Logic ---

#         if is_match:
#             logger.info(f"MATCH FOUND! User: {sub.user.telegram_id}, Sub ID: {sub.id}, Msg ID: {message_schema.id}")
            
#             notification_text = (
#                 f"🔥 <b>New Match Found!</b>\n\n"
#                 f"<b>Channel:</b> {channel_data.name}\n"
#                 f"<b>Subscription:</b> '{sub.query_text}'\n\n"
#                 f"<blockquote>{message_schema.content[:500]}</blockquote>\n"
#                 f"<a href='{message_schema.clickable_link}'>Go to Message</a>"
#             )
            
#             await send_telegram_notification(
#                 user_telegram_id=sub.user.telegram_id,
#                 message=notification_text
#             )

async def run_matching_for_message(message_schema: schemas.MessageCreate, channel_data: schemas.ChannelCreate):
    """
    The dedicated AI matching engine using vector similarity.
    """
    SIMILARITY_THRESHOLD = np.float64(0.6)  # Tune this value (0.6 is broader, 0.8 is stricter)

    # Step 1: Generate the embedding for the new message
    logger.info(f"Matcher: Running for message {message_schema.content[:50]}... from '{channel_data.name}'")
    message_embedding = generate_embedding(message_schema.content)

    # Step 2: Get all subscription embeddings from the database
    with UnitOfWork() as uow:
        # The repo eagerly loads the user data in one query
        subs_orm = uow.subscriptions.get_all_active_subscription_embeddings()
        # Create a simple list of tuples: (subscription_object, embedding_vector)
        subs_with_embeddings = [
            (schemas.Subscription.model_validate(sub), sub.embedding) for sub in subs_orm
        ]
        logger.info(f"Found {len(subs_with_embeddings)} active subscriptions with embeddings.")

    if not subs_with_embeddings:
        logger.info("Matcher: No active subscriptions with embeddings. Nothing to do.")
        return

    # Step 3: Loop and find matches using cosine similarity
    for sub, sub_embedding_list in subs_with_embeddings:
        # Cosine distance is 0 for identical, 1 for opposite.
        # Similarity is 1 - distance.        
        logger.debug(f"Subscription '{sub.query_text}' embedding")
        # Convert to NumPy arrays for calculation
        try:
            msg_vector = np.array(message_embedding)
            sub_vector = np.array(sub_embedding_list)

            # Defensive check for vector dimensions before calculating similarity
            logger.debug(f"Message vector shape:, Subscription vector shape: ")
        except Exception as e:
            logger.error(f"Error converting embeddings to arrays: {e}")
            continue
        
        if msg_vector.shape != sub_vector.shape:
            logger.error(
                f"Embedding shape mismatch for sub '{sub.query_text}'. "
            )
            continue

        logger.info(f"Comparing message '{message_schema.content[:50]}...' with subscription '{sub.query_text}'")
        similarity = 1 - cosine(msg_vector, sub_vector)

        if similarity >= SIMILARITY_THRESHOLD:
            # --- MATCH FOUND! ---
            redirect_link = create_clickable_link(
                channel_telegram_id=channel_data.telegram_id,
                telegram_message_id=message_schema.telegram_message_id
            )
            # The rest of the notification logic is the same.
            user_telegram_id = sub.user.telegram_id # Get from eagerly loaded user
            logger.info(f"AI MATCH FOUND! User: {user_telegram_id}, Similarity: ")
            # ... (call send_telegram_notification) ...
            notification_text = (
                f"🔥 <b>New Match Found!</b>\n\n"
                f"<b>Channel:</b> {channel_data.name}\n"
                f"<b>Subscription:</b> '{sub.query_text}'\n\n"
                f"<blockquote>{message_schema.content[:50]}</blockquote>\n"
                f"<a href='{redirect_link}'>Go to Message</a>"
            )
            
            await send_telegram_notification(
                user_telegram_id=sub.user.telegram_id,
                message=notification_text
            )
        else:
            logger.debug(f"No match for message {message_schema.content[:50]}... (Similarity: )")

def create_clickable_link(channel_telegram_id, telegram_message_id) -> str:
        """
        Generates a clickable t.me link for the message.
        Handles public and private channels/supergroups.
        Returns a non-link placeholder for basic groups.
        """
        # A channel/supergroup ID is always less than -1000000000000
        is_supergroup_or_channel = (channel_telegram_id < -1_000_000_000_000)

        if is_supergroup_or_channel:
            # For supergroups and channels, the link format is t.me/c/...
            simple_channel_id = abs(channel_telegram_id) - 1_000_000_000_000
            return f"https://t.me/c/{simple_channel_id}/{telegram_message_id}"
        else:
            # Basic groups do not have a standard, constructible public link to a specific message.
            # We return a link to the chat itself, which is the best we can do.
            # Note: This link might not work on all clients for private basic groups.
            return f"https://t.me/c/{abs(channel_telegram_id)}/{telegram_message_id}"