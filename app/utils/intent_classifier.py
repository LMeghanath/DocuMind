import os
import pickle
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from django.conf import settings

logger = logging.getLogger(__name__)

# Very simple and small dummy academic dataset for demonstration
DUMMY_DATA = [
    # In-domain (academic, document queries, summaries, definitions, explanations)
    ("What is the summary of this document?", "in-domain"),
    ("Explain the main concept in the text.", "in-domain"),
    ("What does the author mean by this?", "in-domain"),
    ("Find the definition of photosynthesis.", "in-domain"),
    ("What are the key points?", "in-domain"),
    ("Tell me about the history mentioned in the file.", "in-domain"),
    ("Can you extract the conclusion?", "in-domain"),
    ("List the advantages described.", "in-domain"),
    ("Who are the main characters?", "in-domain"),
    ("What is the methodology used?", "in-domain"),

    # Out-of-domain (small talk, general unrelated knowledge, personal questions, actions)
    ("What is the weather today?", "out-of-domain"),
    ("Tell me a funny joke.", "out-of-domain"),
    ("How do I fix my sink?", "out-of-domain"),
    ("Who won the superbowl?", "out-of-domain"),
    ("Where is Paris located?", "out-of-domain"),
    ("What's your favorite color?", "out-of-domain"),
    ("Generate a recipe for chocolate cake.", "out-of-domain"),
    ("How do I hack a website?", "out-of-domain"),
    ("Translate this to French.", "out-of-domain"),
    ("Play some music for me.", "out-of-domain"),
]

def train_and_save_model():
    """
    Trains a simple Logistic Regression model to classify queries as in-domain or out-of-domain.
    Saves the pipeline to ml_models/intent_model.pkl.
    """
    try:
        X, y = zip(*DUMMY_DATA)
        
        # Create a pipeline with TF-IDF and Logistic Regression
        pipeline = Pipeline([
            ('tfidf', TfidfVectorizer(lowercase=True, stop_words='english')),
            ('classifier', LogisticRegression(random_state=42))
        ])
        
        pipeline.fit(X, y)
        
        model_dir = os.path.join(settings.BASE_DIR, 'ml_models')
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, 'intent_model.pkl')
        
        with open(model_path, 'wb') as f:
            pickle.dump(pipeline, f)
            
        logger.info(f"Intent Classifier trained and saved to {model_path}")
        return True
    except Exception as e:
        logger.error(f"Error training intent classifier: {str(e)}")
        return False

def classify_intent(query):
    """
    Loads the trained model and predicts the intent of the query.
    Returns: 'in-domain' or 'out-of-domain'
    """
    try:
        model_path = os.path.join(settings.BASE_DIR, 'ml_models', 'intent_model.pkl')
        
        # If model doesn't exist, train it first
        if not os.path.exists(model_path):
            success = train_and_save_model()
            if not success:
                # Fail gracefully, assume in-domain to allow RAG to try answering 
                return "in-domain" 
                
        with open(model_path, 'rb') as f:
            pipeline = pickle.load(f)
            
        prediction = pipeline.predict([query])[0]
        return prediction
        
    except Exception as e:
        logger.error(f"Error classifying intent: {str(e)}")
        # Fallback
        return "in-domain"
