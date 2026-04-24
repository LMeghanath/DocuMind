import json
import os
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def get_faiss_store_dir(user_id, doc_id=None):
    """Returns the dir containing the FAISS index files for a user or a specific document."""
    user_dir = os.path.join(settings.INDEX_ROOT, str(user_id))
    if doc_id is not None:
        user_dir = os.path.join(user_dir, str(doc_id))
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def get_doc_metadata_path(user_id, doc_id):
    """Returns the path to a specific document's metadata file."""
    user_dir = get_faiss_store_dir(user_id, doc_id)
    return os.path.join(user_dir, f'{doc_id}_meta.json')

def load_doc_metadata(user_id, doc_id):
    """Loads existing metadata for a document securely."""
    path = get_doc_metadata_path(user_id, doc_id)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if data else {}
        except Exception as e:
            logger.error(f"Error loading metadata for user {user_id}, doc {doc_id}: {str(e)}")
            return {}
    return {}

def save_doc_metadata(user_id, doc_id, metadata_dict):
    """Saves the comprehensive metadata dictionary to a JSON file truly atomically."""
    path = get_doc_metadata_path(user_id, doc_id)
    temp_path = path + ".tmp"
    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_dict, f, indent=4)
            
        # os.replace provides atomic swap on POSIX and Windows
        os.replace(temp_path, path)
        return True
    except Exception as e:
        logger.error(f"Error saving metadata for user {user_id}, doc {doc_id}: {str(e)}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False
        
def add_chunks_to_metadata(user_id, doc_id, chunks, start_index=0):
    """
    Creates/Appends chunks to the document's metadata JSON.
    Each chunk gets an integer ID corresponding to its index in the FAISS store.
    chunks: list of LangChain Document objects
    """
    try:
        metadata = load_doc_metadata(user_id, doc_id)
        metadata = metadata or {}  # Extra safety against overwrite bug
        current_index = start_index

        for chunk in chunks:
            # We store chunk_id, document_name, text and page specifically
            metadata[str(current_index)] = {
                "chunk_id": current_index,
                "document_name": chunk.metadata.get("source", "Unknown Document"),
                "page": chunk.metadata.get("page", 0),
                "text": chunk.page_content
            }
            current_index += 1

        return metadata
    except Exception as e:
        logger.error(f"Error structuring metadata for doc {doc_id}: {str(e)}")
        raise e
