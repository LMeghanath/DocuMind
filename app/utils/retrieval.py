import logging
from .faiss_store import load_or_create_faiss
from .embeddings import get_embeddings_model

logger = logging.getLogger(__name__)

def retrieve_context(query, user_id, k=4, similarity_threshold=0.75):
    """
    Retrieves the most relevant chunks from the FAISS vector store.
    Filters out chunks below the similarity_threshold.
    Returns "Not in documents" if nothing matches.
    """
    try:
        vector_store = load_or_create_faiss(user_id)
        if vector_store is None:
            return "Not in documents"

        # Search FAISS (using similarity_search_with_score which returns L2 distance by default in FAISS)
        # Note: In L2 distance, lower score is better (more similar). 
        # But we will use similarity_search_with_relevance_scores if available, 
        # where higher is better, bounded between 0 and 1.
        
        # We will use score_threshold directly in the search to keep it simple
        retriever = vector_store.as_retriever(
            search_type="similarity_score_threshold",
            search_kwargs={
                "k": k,
                "score_threshold": similarity_threshold
            }
        )
        
        docs = retriever.invoke(query)
        
        if not docs:
            return "Not in documents"

        # Build clean context string, respecting a simple token limit approximation
        # (e.g., 4 chunks * 500 tokens = 2000 tokens max context)
        context_parts = []
        for doc in docs:
            # Append document source for better LLM grounding if desired
            source = doc.metadata.get("source", "Unknown")
            context_parts.append(f"--- Document: {source} ---\n{doc.page_content}")
            
        final_context = "\n\n".join(context_parts)
        
        # Basic token limit safeguard (assuming roughly 4 chars per token)
        max_context_length_chars = 2500 * 4 
        if len(final_context) > max_context_length_chars:
            final_context = final_context[:max_context_length_chars] + "\n...[Context Truncated]..."
            
        return final_context

    except Exception as e:
        logger.error(f"Error retrieving context for user {user_id}: {str(e)}")
        # If there is an issue with the index or threshold algorithm fails depending on distance metric,
        # fallback to basic k-nearest
        try:
            docs = vector_store.similarity_search(query, k=k)
            if not docs:
                 return "Not in documents"
            return "\n\n".join([doc.page_content for doc in docs])
        except Exception as fallback_e:
             logger.error(f"Fallback retrieval failed: {str(fallback_e)}")
             return "Not in documents"
