import os
import logging
from langchain_openai import OpenAIEmbeddings
from django.conf import settings

logger = logging.getLogger(__name__)

# Single instance of embeddings model for the app to reuse
# We are using OpenAI API as requested. It requires OPENAI_API_KEY environment variable.
def get_embeddings_model():
    """Returns the text embedding model instance."""
    try:
        # Simple academic setup - expects OPENAI_API_KEY in .env or environment
        return OpenAIEmbeddings()
    except Exception as e:
        logger.error(f"Error initializing embeddings model: {str(e)}")
        raise e
