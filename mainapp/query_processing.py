from django.shortcuts import redirect
from django.contrib import messages
from .models import Chat, Message
from django.shortcuts import get_object_or_404


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

        if chat.chat_title == "Untitled Chat":
            chat.chat_title = message[:60]
            chat.save()

        from .utils.faiss_store import load_or_create_faiss
        
        SIMILARITY_THRESHOLD = 0.8  # lower score = more similar in FAISS L2 distance
        context_parts = []
        for doc_id_str in user_selected_docs:
            try:
                # Fetch original file name from database for clean citations
                from .models import Document
                db_doc = Document.objects.filter(id=int(doc_id_str), user=request.user).first()
                display_source = db_doc.display_name if db_doc else "Unknown Document"

                vector_store = load_or_create_faiss(request.user.id, int(doc_id_str))
                if vector_store:
                    results = vector_store.similarity_search_with_score(message, k=4)
                    for doc, score in results:
                        # We removed the strict score limit here so the LLM always gets some context to work with.
                        context_parts.append(
                            f"SOURCE: {display_source}\nCONTENT: {doc.page_content}"
                        )
            except Exception as e:
                pass
        
        # Join chunks with a clear separator, or signal nothing was found
        context = "\n\n---\n\n".join(context_parts) if context_parts else "Not in documents"

        # Generate response — hallucination guardrail lives inside generate_response
        try:
            from .utils.llm_integration import generate_response
            ai_response = generate_response(query=message, context=context)
            print("\n\n\n\n\n"+f"final context {context}")
        except Exception as e:
            print(e)
            ai_response = f"Failed to call LLM: {str(e)}"
        
        Message.objects.create(
            chat=chat,
            role="assistant",
            message_text=ai_response
        )

    return redirect("chatpage", chat_id)
