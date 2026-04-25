import re
import logging

logger = logging.getLogger(__name__)

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

        # 2. Less aggressive cleaning - keep alphanumeric, basic punctuation, emails, and slash
        text = re.sub(r'[^\w\s.,@:/-]', '', text)

        # 3. Remove extra spaces and newlines
        text = re.sub(r'\s+', ' ', text)

        # 4. Strip leading/trailing whitespaces
        text = text.strip()

        return text
    except Exception as e:
        logger.error(f"Error during preprocessing: {str(e)}")
        # In case of error, return original text to avoid complete failure
        return str(text) if text else ""
