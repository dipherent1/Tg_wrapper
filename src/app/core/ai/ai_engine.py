# src/app/core/ai_engine.py
import logging
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)
_model = None

def get_embedding_model() -> SentenceTransformer:
    """
    Loads and returns the sentence-transformer model.
    Loads it only once and caches it in memory.
    """
    global _model
    if _model is None:
        logger.info("Loading AI embedding model into memory...")
        # This is a small, fast, and very effective model.
        model_name = 'all-MiniLM-L6-v2'
        _model = SentenceTransformer(model_name)
        logger.info("AI embedding model loaded successfully.")
    return _model

def generate_embedding(text: str) -> list[float]:
    """Generates a vector embedding for a given piece of text."""
    model = get_embedding_model()
    embedding = model.encode(text, convert_to_tensor=False)
    # convert_to_tensor=False gives a numpy array, .tolist() makes it a simple list
    return embedding.tolist()