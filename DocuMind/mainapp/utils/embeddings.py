import os
import logging
from langchain_huggingface import HuggingFaceEmbeddings
from django.conf import settings

logger = logging.getLogger(__name__)

_embedding_model = None

# Single instance of embeddings model for the app to reuse
def get_embeddings_model():
    """Returns the text embedding model instance using HuggingFace."""
    global _embedding_model
    try:
        # We use a fast, local sentence-transformer model
        if _embedding_model is None:
            _embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        return _embedding_model
    except Exception as e:
        logger.error(f"Error initializing embeddings model: {str(e)}")
        raise e
