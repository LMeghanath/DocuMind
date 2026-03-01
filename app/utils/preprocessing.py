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
