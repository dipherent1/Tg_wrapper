# src/app/core/ai_engine.py
import logging
from app.config.config import settings
import google.generativeai as genai

logger = logging.getLogger(__name__)


try:
    if settings.GEMINI_API_KEY:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        logger.info("Gemini AI client configured successfully.")
    else:
        logger.warning("GEMINI_API_KEY not found. AI embedding generation is disabled.")
except Exception as e:
    logger.error(f"Failed to configure Gemini AI client: {e}", exc_info=True)


def generate_embedding(text: str, task_type: str) -> list[float] | None:
    """
    Generates a vector embedding for a given piece of text using the Gemini API.
    
    Args:
        text: The text to embed.
        task_type: Either 'RETRIEVAL_QUERY' (for user searches) or 
                   'RETRIEVAL_DOCUMENT' (for messages to be stored/searched against).
    """
    if not settings.GEMINI_API_KEY or not text:
        return None
        
    try:
        # 'text-embedding-004' is the recommended model, producing 768 dimensions.
        result = genai.embed_content(
            model="models/text-embedding-004",
            content=text,
            task_type=task_type
        )
        return result['embedding']
    except Exception as e:
        logger.error(f"Error generating embedding from Gemini API for text '{text[:50]}...': {e}")
        return None
