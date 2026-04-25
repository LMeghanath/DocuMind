import os
import logging
from langchain_community.vectorstores import FAISS
from django.conf import settings
from .embeddings import get_embeddings_model
from .metadata_handler import add_chunks_to_metadata, save_doc_metadata, get_faiss_store_dir

logger = logging.getLogger(__name__)

def load_or_create_faiss(user_id, doc_id):
    """
    Loads existing FAISS index for a specific document, or creates a new empty one 
    if it doesn't exist yet. Returns None if creating empty.
    """
    store_dir = get_faiss_store_dir(user_id, doc_id)
    embeddings = get_embeddings_model()
    
    # LangChain FAISS save_local creates {index_name}.faiss and {index_name}.pkl
    # We will use doc_id as the index_name.
    index_name = str(doc_id)
    
    if os.path.exists(os.path.join(store_dir, f"{index_name}.faiss")):
        try:
            return FAISS.load_local(store_dir, embeddings, index_name=index_name, allow_dangerous_deserialization=True)
        except Exception as e:
            logger.error(f"Error loading FAISS index for doc {doc_id}: {str(e)}")
            return None
    return None

def save_faiss_and_metadata_atomically(user_id, doc_id, vector_store, custom_metadata_dict):
    """
    Saves both the FAISS index and the JSON metadata to disk for a specific document.
    """
    store_dir = get_faiss_store_dir(user_id, doc_id)
    index_name = str(doc_id)
    try:
        # Save FAISS -> creates {doc_id}.faiss and {doc_id}.pkl
        vector_store.save_local(store_dir, index_name=index_name)
        
        # Save JSON metadata explicitly as requested -> {doc_id}_meta.json
        save_success = save_doc_metadata(user_id, doc_id, custom_metadata_dict)
        if not save_success:
            raise Exception("Failed to save JSON metadata.")
            
        return True
    except Exception as e:
        logger.error(f"Atomic save failed for doc {doc_id}: {str(e)}")
        # Rollback FAISS files to maintain atomic constraints
        for ext in ['.faiss', '.pkl']:
            fpath = os.path.join(store_dir, f"{doc_id}{ext}")
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except:
                    pass
        raise e

def add_documents_to_store(user_id, doc_id, chunks):
    """
    Takes text chunks, embeds them, adds to FAISS, builds metadata JSON,
    and calls atomic save. Now done per-document.
    """
    try:
        embeddings = get_embeddings_model()
        vector_store = load_or_create_faiss(user_id, doc_id)
        
        start_index = 0
        
        if vector_store is None:
            # First time creating store for this document
            vector_store = FAISS.from_documents(chunks, embeddings)
        else:
            # Get current size to continue IDs
            start_index = vector_store.index.ntotal
            vector_store.add_documents(chunks)
            
        # Update our specific JSON metadata format per document
        updated_metadata = add_chunks_to_metadata(user_id, doc_id, chunks, start_index)
        
        # Atomically save FAISS and Metadata
        save_success = save_faiss_and_metadata_atomically(user_id, doc_id, vector_store, updated_metadata)
        if not save_success:
            raise Exception("Failed to save to vector store.")
            
        return True
    except Exception as e:
        logger.error(f"Error adding documents to store for doc {doc_id}: {str(e)}")
        raise e
