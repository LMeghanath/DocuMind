import os
import hashlib
from threading import Lock
import logging

logger = logging.getLogger(__name__)

# Simple lock to simulate queue handling and prevent race conditions for identical user uploads
upload_locks = {}
lock_manager = Lock()

def get_user_lock(user_id):
    with lock_manager:
        if user_id not in upload_locks:
            upload_locks[user_id] = Lock()
        return upload_locks[user_id]

def allowed_file(filename):
    """Check if file format is supported."""
    allowed_extensions = {'.pdf', '.txt'}
    ext = os.path.splitext(filename)[1].lower()
    return ext in allowed_extensions

def calculate_file_hash(file_content):
    """Calculate SHA-256 hash of file content to detect duplicates."""
    hasher = hashlib.sha256()
    hasher.update(file_content)
    return hasher.hexdigest()

def handle_uploaded_file(file, user_id):
    """Handles the file upload process with basic validations."""
    try:
        if not file:
            return False, "Empty file"

        if not allowed_file(file.name):
            return False, f"Unsupported format. Allowed formats: .pdf, .txt"

        content = file.read()
        
        # Check if empty content
        if not content or len(content) < 10:
            return False, "Empty document or very low text content."
            
        # Reset file pointer after reading
        file.seek(0)
        
        # NOTE: Duplicate checking against the DB or FAISS index happens in views or a higher layer.
        
        return True, "File is valid"
    except Exception as e:
        logger.error(f"Error handling file upload: {str(e)}")
        return False, f"Error processing file: {str(e)}"
