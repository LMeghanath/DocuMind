import os
import logging
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from django.conf import settings

logger = logging.getLogger(__name__)

# Single instance of embeddings model for the app to reuse
def get_embeddings_model():
    """Returns the text embedding model instance from Google."""
    try:
        # Academic setup - expects GOOGLE_API_KEY in .env or environment
        return GoogleGenerativeAIEmbeddings(
            model="models/embedding-001",
            google_api_key=os.getenv("GOOGLE_API_KEY")
        )
    except Exception as e:
        logger.error(f"Error initializing embeddings model: {str(e)}")
        raise e
