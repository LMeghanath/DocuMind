import os
import logging
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)


def get_llm():
    """Returns the Gemini LLM instance via LangChain."""
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",  # Use 'gemini-2.5-flash-lite' if you hit quota
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.3,  # Low temperature ensures academic accuracy
    )


def generate_response(query, context):
    """
    Module 5: Text Generation
    Takes the query and pre-built context string, then generates a cited answer
    using a LangChain LCEL chain with a hallucination guardrail.
    """
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key or api_key == "your_gemini_api_key_here":
            return "Error: Please update GOOGLE_API_KEY in your `.env` file with a valid Gemini API key!"

        # Hallucination guardrail — bail early if retrieval found nothing
        if not context or context.strip() in ("Not in documents", "No documents found."):
            return "I'm sorry, I couldn't find any information regarding that in your documents."

        # System prompt — instructs the model to cite source filenames
        template = """
You are a professional academic assistant. Use ONLY the provided context to answer.

RULES:
- Cite the source filename for every fact (e.g., "According to [filename]...").
- If the answer is not in the context, say "I cannot find this in the documents."
- Maintain a formal, academic tone.

Context:
{context}

Question: {question}

Answer:"""

        prompt = ChatPromptTemplate.from_template(template)
        llm = get_llm()

        # LCEL chain: inject pre-fetched context + passthrough question
        chain = (
            {"context": lambda x: context, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )

        return chain.invoke(query)

    except Exception as e:
        logger.error(f"Error during text generation: {str(e)}")
        if "429" in str(e):
            return "Quota exceeded. Please wait a minute before retrying."
        return "A generation error occurred. Please try again later."
