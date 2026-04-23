from django.shortcuts import redirect
from django.contrib import messages
from .models import Chat, Message
from django.shortcuts import get_object_or_404
# If you have an LLM or rag logic it goes here

def user_query_processing(request, chat_id):
    if request.method == "POST":
        message = request.POST.get("query_holder","").strip().lower()

        if not message:
            messages.error(request, "Query can't be empty!")
            return redirect("chatpage", chat_id)

        user_selected_docs = request.session.get("user_selected_docs")
        if not user_selected_docs:
            messages.error(request, "Please select at least one document to query!")
            return redirect("chatpage", chat_id)

        chat = get_object_or_404(Chat, id=chat_id, user=request.user)

        Message.objects.create(
            chat=chat,
            role="user",
            message_text=message
        )

        if chat.chat_title == "New Chat":
            chat.chat_title = message[:60]
            chat.save()

        from .utils.faiss_store import load_or_create_faiss
        
        # Build context from FAISS
        context_snippets = []
        for doc_id_str in user_selected_docs:
            try:
                vector_store = load_or_create_faiss(request.user.id, int(doc_id_str))
                if vector_store:
                    results = vector_store.similarity_search(message, k=2)
                    for res in results:
                        context_snippets.append(res.page_content)
            except Exception as e:
                pass
                
        context = "\n".join(context_snippets)

        # Retrieve context...
        if context:
            try:
                from .utils.llm_integration import generate_response
                ai_response = generate_response(query=message, context=context)
            except Exception as e:
                ai_response = f"Failed to call LLM: {str(e)}"
        else:
            ai_response = f"I've received your query: {message}. No relevant context could be extracted from the selected documents."

        Message.objects.create(
            chat=chat,
            role="assistant",
            message_text=ai_response
        )

    return redirect("chatpage", chat_id)
