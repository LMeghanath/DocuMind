import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from django.conf import settings

logger = logging.getLogger(__name__)

# Very basic Prompt Injection filter for academic project
FORBIDDEN_PHRASES = [
    "ignore previous",
    "forget previous",
    "disregard previous",
    "system prompt",
    "you are now",
    "ignore all instructions"
]

def check_prompt_injection(query):
    """
    Basic protection against simple prompt injections.
    Returns True if safe, False if potentially malicious.
    """
    query_lower = query.lower()
    for phrase in FORBIDDEN_PHRASES:
        if phrase in query_lower:
            return False
    return True

def get_llm_response(query, context):
    """
    Sends the user query along with retrieved context to the LLM.
    Uses the strictly defined prompt format.
    """
    try:
        # 1. Prompt Injection Protection
        if not check_prompt_injection(query):
            return "Security Alert: Query rejected due to potential prompt injection."

        # 2. Strict Prompt as requested
        prompt = f"""
Answer ONLY using the context.

Context:
{context}

Question:
{query}

If not found, say: Not in documents.
"""

        # 3. LLM API Call
        llm = ChatGoogleGenerativeAI(temperature=0, model="gemini-1.5-flash")
        
        response = llm.invoke(prompt)
        return response.content
        
    except Exception as e:
        logger.error(f"Error communicating with LLM: {str(e)}")
        # Adding a friendly error instead of crashing
        return "Sorry, I am currently unable to generate a response. Please check the API configuration."
