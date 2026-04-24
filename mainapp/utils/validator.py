import os
import hashlib
import fitz  # PyMuPDF
import logging
from app.models import Document

logger = logging.getLogger(__name__)

def calculate_file_hash(file_obj):
    """Calculate SHA-256 hash of file content safely without loading entire file into memory."""
    hasher = hashlib.sha256()
    for chunk in file_obj.chunks():
        hasher.update(chunk)
    return hasher.hexdigest()

def validate_file(uploaded_file, user):
    """
    Validates the uploaded file with safe memory handling.
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

        # Reset pointer after chunk testing
        uploaded_file.seek(0)
        
        # 2. Duplicate Check using memory-safe hashing
        file_hash = calculate_file_hash(uploaded_file)
        
        if Document.objects.filter(user=user, file_hash=file_hash).exists():
            return False, "You have already uploaded exactly this document (Duplicate).", file_hash

        # 3. PDF Integrity
        if ext == '.pdf':
            try:
                # Use temporary file path if available to prevent reading large PDFs into memory
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
        # Guarantee file pointer is always reset regardless of early return or error
        uploaded_file.seek(0)
