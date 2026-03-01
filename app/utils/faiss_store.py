import os
import logging
from langchain_community.vectorstores import FAISS
from django.conf import settings
from .embeddings import get_embeddings_model
from .metadata_handler import add_chunks_to_metadata, save_user_metadata, get_user_metadata_path

logger = logging.getLogger(__name__)

def get_faiss_index_path(user_id):
    """Returns path for FAISS index."""
    user_dir = os.path.join(settings.BASE_DIR, 'vector_store', str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, 'index.bin')

def get_faiss_store_path(user_id):
    """Returns the dir containing the FAISS index files for saving/loading."""
    user_dir = os.path.join(settings.BASE_DIR, 'vector_store', str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def load_or_create_faiss(user_id):
    """
    Loads existing FAISS index for user, or creates a new empty one 
    if it doesn't exist yet. We return None if creating empty so we can 
    initialize it with the first batch of documents.
    """
    store_path = get_faiss_store_path(user_id)
    embeddings = get_embeddings_model()
    
    # LangChain FAISS save_local creates index.faiss and index.pkl
    # We will use this built in functionality and store them in the user's directory.
    if os.path.exists(os.path.join(store_path, "index.faiss")):
        try:
            return FAISS.load_local(store_path, embeddings, allow_dangerous_deserialization=True)
        except Exception as e:
            logger.error(f"Error loading FAISS index for user {user_id}: {str(e)}")
            return None
    return None

def save_faiss_and_metadata_atomically(user_id, vector_store, custom_metadata_dict):
    """
    Saves both the FAISS index and the JSON metadata to disk sequentially.
    Since we are constrained to simple academic architecture, we try-catch to 
    ensure both succeed or we log an error. true 'atomic' operations on separate files 
    require OS level transaction or staging files, which is too complex here.
    """
    store_path = get_faiss_store_path(user_id)
    try:
        # Save FAISS
        vector_store.save_local(store_path)
        
        # Save JSON metadata explicitly as requested
        save_success = save_user_metadata(user_id, custom_metadata_dict)
        if not save_success:
            raise Exception("Failed to save JSON metadata.")
            
        return True
    except Exception as e:
        logger.error(f"Atomic save failed for user {user_id}: {str(e)}")
        return False

def add_documents_to_store(user_id, chunks):
    """
    Takes text chunks, embeds them, adds to FAISS, builds metadata JSON,
    and calls atomic save.
    """
    try:
        embeddings = get_embeddings_model()
        vector_store = load_or_create_faiss(user_id)
        
        start_index = 0
        
        if vector_store is None:
            # First time creating store for this user
            vector_store = FAISS.from_documents(chunks, embeddings)
        else:
            # Get current size to continue IDs
            start_index = vector_store.index.ntotal
            vector_store.add_documents(chunks)
            
        # Update our specific JSON metadata format as requested
        updated_metadata = add_chunks_to_metadata(user_id, chunks, start_index)
        
        # Atomically save FAISS and Metadata
        save_success = save_faiss_and_metadata_atomically(user_id, vector_store, updated_metadata)
        if not save_success:
            raise Exception("Failed to save to vector store.")
            
        return True
    except Exception as e:
        logger.error(f"Error adding documents to store for user {user_id}: {str(e)}")
        raise e
