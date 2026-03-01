import json
import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def get_user_metadata_path(user_id):
    """Returns the path to the user's single metadata file."""
    # Assuming vector_store/user_id/ dir structure will be created here too or in faiss_store
    user_dir = os.path.join(settings.BASE_DIR, 'vector_store', str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, 'metadata.json')

def load_user_metadata(user_id):
    """Loads existing metadata for a user."""
    path = get_user_metadata_path(user_id)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading metadata for user {user_id}: {str(e)}")
            return {}
    return {}

def save_user_metadata(user_id, metadata_dict):
    """Saves the comprehensive metadata dictionary to a JSON file."""
    path = get_user_metadata_path(user_id)
    try:
        # Atomic save is technically harder with pure JSON in python without a temp file approach, 
        # but for academic level we'll use a direct write. 
        # (Module 6 asks for FAISS + JSON atomic save, handled there).
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(metadata_dict, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error saving metadata for user {user_id}: {str(e)}")
        return False
        
def add_chunks_to_metadata(user_id, chunks, start_index=0):
    """
    Appends new chunks to the user's metadata JSON.
    Each chunk gets an integer ID corresponding to its index in the FAISS store.
    chunks: list of LangChain Document objects
    """
    try:
        metadata = load_user_metadata(user_id)
        current_index = start_index

        for chunk in chunks:
            # We store chunk_id, document_name, text as requested
            metadata[str(current_index)] = {
                "chunk_id": current_index,
                "document_name": chunk.metadata.get("source", "Unknown Document"),
                "text": chunk.page_content
            }
            current_index += 1

        # We don't save here immediately if we need atomic save with FAISS in Module 6. 
        # We will return the updated metadata dict instead.
        return metadata
    except Exception as e:
        logger.error(f"Error structuring metadata for user {user_id}: {str(e)}")
        raise e
