"""
================================================================================
TEAM EXPORT: ContextIQ Modules 4, 5, and 6 (Production Ready)
================================================================================
This file contains the complete logic for:
- MODULE 3.5: Validation (Memory Safety, File Hash, Integrity)
- MODULE 4: Preprocessing (Safe Text Cleaning)
- MODULE 5: Text Extraction + Chunking (Optimized Chunk Size + Page Metadata)
- MODULE 6: Embeddings + FAISS (Per-Document Indices, Atomic Storage, HuggingFace)

DEPENDENCIES REQUIRED:
Add these to your requirements.txt or pip install them:
    pip install langchain-community langchain-text-splitters pypdf faiss-cpu fitz PyMuPDF langchain-huggingface sentence-transformers

INTEGRATION INSTRUCTIONS:
1. Use `@transaction.atomic` in your file upload views.
2. In your File Upload View:
    - Validate the file via `validate_file`.
    - If valid, save the DB Document.
    - Call `extract_and_chunk_file(file_path)`
    - Pass the resulting chunks to `add_documents_to_store(user_id, doc_id, chunks)`
    - Update `document.is_processed = True`
================================================================================
"""

import os
import re
import json
import logging
import hashlib
from django.conf import settings
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

# ==============================================================================
# PRE-PROCESSING: File Validation
# ==============================================================================

def calculate_file_hash(file_obj):
    """Calculate SHA-256 hash safely without loading entire file into memory."""
    hasher = hashlib.sha256()
    for chunk in file_obj.chunks():
        hasher.update(chunk)
    return hasher.hexdigest()

def validate_file(uploaded_file):
    """
    Validates an uploaded file format, size, content quality, and PDF integrity.
    NOTE: DB duplicate checking using file_hash is handled at the View layer.
    """
    try:
        # 1. Size / Type Check
        allowed_extensions = {'.pdf', '.txt'}
        ext = os.path.splitext(uploaded_file.name)[1].lower()
        if ext not in allowed_extensions:
            return False, "Unsupported file format. Only PDF and TXT are allowed.", None

        # Size check (e.g., max 10MB)
        MAX_SIZE = 10 * 1024 * 1024
        if uploaded_file.size > MAX_SIZE:
            return False, "File is too large. Maximum size is 10MB.", None

        # Content quality check safely (prevent memory abuse and string concat lag)
        sample_chunks = []
        for chunk in uploaded_file.chunks():
            sample_chunks.append(chunk)
            if sum(len(c) for c in sample_chunks) > 100:
                break
        sample_text = b"".join(sample_chunks)
        if len(sample_text.strip()) < 50:
            return False, "File is virtually empty or very low content.", None

        uploaded_file.seek(0)
        file_hash = calculate_file_hash(uploaded_file)

        # 2. PDF Integrity
        if ext == '.pdf':
            try:
                # Use temp path if available or capped 1MB stream to save memory
                if hasattr(uploaded_file, 'temporary_file_path'):
                    doc = fitz.open(uploaded_file.temporary_file_path())
                else:
                    uploaded_file.seek(0)
                    doc = fitz.open(stream=uploaded_file.read(1024 * 1024), filetype="pdf")
                    
                if doc.needs_pass:
                    return False, "PDF is encrypted/password protected.", file_hash
                if doc.page_count == 0:
                    return False, "PDF has zero pages.", file_hash
                doc.close()
            except Exception as e:
                logger.error(f"PDF Parsing error: {str(e)}")
                return False, f"Invalid or corrupted PDF file: {str(e)}", file_hash

        return True, "Valid", file_hash

    except Exception as e:
        logger.error(f"Validation error: {str(e)}")
        return False, f"Error validating file: {str(e)}", None
        
    finally:
        # Guarantee file pointer reset prevents silent downstream pipeline failures
        uploaded_file.seek(0)


# ==============================================================================
# MODULE 4: Preprocessing
# ==============================================================================

def preprocess_text(text):
    """Cleans text efficiently while keeping vital symbols."""
    try:
        if not text:
            return ""

        text = text.lower()
        # Keep alphanumeric, basic punctuation, emails, slashes
        text = re.sub(r'[^\w\s.,@:/-]', '', text)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    except Exception as e:
        logger.error(f"Error during preprocessing: {str(e)}")
        return str(text) if text else ""


# ==============================================================================
# MODULE 5: Text Extraction + Chunking
# ==============================================================================

def extract_and_chunk_file(file_path):
    """Extracts text using LangChain, cleans it, and applies optimal chunking."""
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

        for i, doc in enumerate(documents):
            doc.page_content = preprocess_text(doc.page_content)
            doc.metadata["source"] = os.path.basename(file_path)
            doc.metadata["page"] = i + 1

        # Better chunk size for embedding performance
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            length_function=len,
            add_start_index=True,
        )

        chunks = text_splitter.split_documents(documents)
        return chunks

    except Exception as e:
        logger.error(f"Error extracting and chunking file {file_path}: {str(e)}")
        raise e


def get_faiss_store_dir(user_id):
    """Returns the dir containing the FAISS index files for a user."""
    user_dir = os.path.join(settings.MEDIA_ROOT, 'indexes', str(user_id))
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def get_doc_metadata_path(user_id, doc_id):
    return os.path.join(get_faiss_store_dir(user_id), f'{doc_id}_meta.json')

def load_doc_metadata(user_id, doc_id):
    path = get_doc_metadata_path(user_id, doc_id)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data if data else {}
        except Exception as e:
            logger.error(f"Error loading metadata: {str(e)}")
            return {}
    return {}

def save_doc_metadata(user_id, doc_id, metadata_dict):
    """Saves the metadata dictionary to a JSON file truly atomically."""
    path = get_doc_metadata_path(user_id, doc_id)
    temp_path = path + ".tmp"
    try:
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(metadata_dict, f, indent=4)
        # Atomic swap
        os.replace(temp_path, path)
        return True
    except Exception as e:
        logger.error(f"Error saving metadata safely: {str(e)}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        return False
        
def add_chunks_to_metadata(user_id, doc_id, chunks, start_index=0):
    """Appends new chunks securely to the document's metadata JSON."""
    try:
        metadata = load_doc_metadata(user_id, doc_id)
        metadata = metadata or {} # Protection against overwrite bug
        current_index = start_index

        for chunk in chunks:
            metadata[str(current_index)] = {
                "chunk_id": current_index,
                "document_name": chunk.metadata.get("source", "Unknown Document"),
                "page": chunk.metadata.get("page", 0),  # Page level metadata recording
                "text": chunk.page_content
            }
            current_index += 1

        return metadata
    except Exception as e:
        logger.error(f"Error structuring metadata: {str(e)}")
        raise e


# ==============================================================================
# MODULE 6: Embeddings + FAISS Storage
# ==============================================================================
_embedding_model = None

def get_embeddings_model():
    """Returns a cached HuggingFace embeddings model for local processing."""
    global _embedding_model
    try:
        if _embedding_model is None:
            _embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        return _embedding_model
    except Exception as e:
        logger.error(f"Error initializing HuggingFace model: {str(e)}")
        raise e

def load_or_create_faiss(user_id, doc_id):
    store_dir = get_faiss_store_dir(user_id)
    embeddings = get_embeddings_model()
    index_name = str(doc_id)
    
    if os.path.exists(os.path.join(store_dir, f"{index_name}.faiss")):
        try:
            return FAISS.load_local(store_dir, embeddings, index_name=index_name, allow_dangerous_deserialization=True)
        except Exception as e:
            logger.error(f"Error loading FAISS index: {str(e)}")
            return None
    return None

def save_faiss_and_metadata_atomically(user_id, doc_id, vector_store, custom_metadata_dict):
    """Saves FAISS index and JSON metadata securely with full rollback capability."""
    store_dir = get_faiss_store_dir(user_id)
    try:
        vector_store.save_local(store_dir, index_name=str(doc_id))
        
        save_success = save_doc_metadata(user_id, doc_id, custom_metadata_dict)
        if not save_success:
            raise Exception("Failed to save JSON metadata atomically.")
        return True
    except Exception as e:
        logger.error(f"Save failed for doc {doc_id}. Initiating FAISS rollback: {str(e)}")
        delete_document_indexes(user_id, doc_id)
        raise e

def add_documents_to_store(user_id, doc_id, chunks):
    try:
        if not chunks:
            return True

        embeddings = get_embeddings_model()
        vector_store = load_or_create_faiss(user_id, doc_id)
        
        start_index = 0
        if vector_store is None:
            vector_store = FAISS.from_documents(chunks, embeddings)
        else:
            start_index = vector_store.index.ntotal
            vector_store.add_documents(chunks)
            
        updated_metadata = add_chunks_to_metadata(user_id, doc_id, chunks, start_index)
        
        save_success = save_faiss_and_metadata_atomically(user_id, doc_id, vector_store, updated_metadata)
        if not save_success:
            raise Exception("Failed to save to vector store.")
            
        return True
    except Exception as e:
        logger.error(f"Error adding documents to store: {str(e)}")
        raise e

# ==============================================================================
# DELETION UTILITY
# ==============================================================================

def delete_document_indexes(user_id, doc_id):
    """Safely deletes vector index files to completely wipe out specific document."""
    try:
        store_dir = get_faiss_store_dir(user_id)
        if not os.path.exists(store_dir):
            return False
            
        faiss_file = os.path.join(store_dir, f"{doc_id}.faiss")
        pkl_file = os.path.join(store_dir, f"{doc_id}.pkl")
        meta_file = os.path.join(store_dir, f"{doc_id}_meta.json")
        
        deleted_any = False
        for file_path in [faiss_file, pkl_file, meta_file]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted sub-index file: {file_path}")
                    deleted_any = True
                except Exception as e:
                    logger.error(f"Error deleting index file {file_path}: {str(e)}")
                    
        return deleted_any
    except Exception as e:
        logger.error(f"Fatal error during document index deletion: {str(e)}")
        return False
