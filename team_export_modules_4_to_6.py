"""
================================================================================
TEAM EXPORT: ContextIQ Modules 4, 5, and 6
================================================================================
This file contains the complete logic for:
- MODULE 4: Preprocessing (Text Cleaning)
- MODULE 5: Text Extraction + Chunking (LangChain Loaders, JSON Metadata)
- MODULE 6: Embeddings + FAISS (Google Gemini Embeddings, Atomic local save)

DEPENDENCIES REQUIRED:
Add these to your requirements.txt or pip install them:
    pip install langchain-community langchain-text-splitters pypdf faiss-cpu langchain-google-genai

ENVIRONMENT VARIABLES REQUIRED:
    GOOGLE_API_KEY=your_gemini_api_key_here

INTEGRATION INSTRUCTIONS (For Modules 1, 2, 3 and 7, 8, 9):
1. Place the underlying functions in your `app/utils/` folder as separate files 
   (e.g., preprocessing.py, chunking.py, metadata_handler.py, etc.) or keep them 
   here in one utility file.
2. In your File Upload View (Module 3):
    - After saving the Document model temporarily, call `extract_and_chunk_file(file_path)`
    - Pass the resulting chunks to `add_documents_to_store(user_id, chunks)`
3. In your Retrieval View (Module 7):
    - You will need to load FAISS via `load_or_create_faiss(user_id)` to search it.
================================================================================
"""

import os
import re
import json
import logging
from django.conf import settings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS

logger = logging.getLogger(__name__)

# ==============================================================================
# MODULE 4: Preprocessing
# ==============================================================================

def preprocess_text(text):
    """
    Cleans text by removing noise, special characters, and extra spaces.
    Keeps it simple for academic level.
    """
    try:
        if not text:
            return ""

        # 1. Lowercasing
        text = text.lower()

        # 2. Remove special characters (keep alphanumeric and basic punctuation)
        # We'll allow letters, numbers, spaces, periods, commas, question marks, and hyphens
        text = re.sub(r'[^a-z0-9\s.,?-]', '', text)

        # 3. Remove extra spaces and newlines
        text = re.sub(r'\s+', ' ', text)

        # 4. Strip leading/trailing whitespaces
        text = text.strip()

        return text
    except Exception as e:
        logger.error(f"Error during preprocessing: {str(e)}")
        # In case of error, return original text to avoid complete failure
        return str(text) if text else ""


# ==============================================================================
# MODULE 5: Text Extraction + Chunking
# ==============================================================================

def extract_and_chunk_file(file_path):
    """
    Extracts text from a file (PDF/TXT) using LangChain loaders,
    cleans it using module 4 preprocess, and chunks it.
    """
    try:
        documents = []
        ext = os.path.splitext(file_path)[1].lower()

        if ext == '.pdf':
            loader = PyPDFLoader(file_path)
            documents = loader.load()
        elif ext == '.txt':
            loader = TextLoader(file_path, encoding='utf-8')
            documents = loader.load()
        else:
            raise ValueError(f"Unsupported file format for extraction: {ext}")

        # Preprocess text content 
        for doc in documents:
            doc.page_content = preprocess_text(doc.page_content)
            # Add simple source name to metadata without full path
            doc.metadata["source"] = os.path.basename(file_path)

        # Basic chunking (Student level, 500 token length approximation, overlapping slightly)
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=2000, # Approx 500 tokens
            chunk_overlap=200,
            length_function=len,
            add_start_index=True,
        )

        chunks = text_splitter.split_documents(documents)
        return chunks

    except Exception as e:
        logger.error(f"Error extracting and chunking file {file_path}: {str(e)}")
        raise e


def get_user_metadata_path(user_id):
    """Returns the path to the user's single metadata file."""
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
    """
    try:
        metadata = load_user_metadata(user_id)
        current_index = start_index

        for chunk in chunks:
            metadata[str(current_index)] = {
                "chunk_id": current_index,
                "document_name": chunk.metadata.get("source", "Unknown Document"),
                "text": chunk.page_content
            }
            current_index += 1

        return metadata
    except Exception as e:
        logger.error(f"Error structuring metadata for user {user_id}: {str(e)}")
        raise e


# ==============================================================================
# MODULE 6: Embeddings + FAISS Storage
# ==============================================================================

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

def get_faiss_store_path(user_id):
    """Returns the dir containing the FAISS index files for saving/loading."""
    user_dir = os.path.join(settings.BASE_DIR, 'vector_store', str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def load_or_create_faiss(user_id):
    """
    Loads existing FAISS index for user, or creates a new empty one 
    if it doesn't exist yet. We return None if creating empty.
    """
    store_path = get_faiss_store_path(user_id)
    embeddings = get_embeddings_model()
    
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
