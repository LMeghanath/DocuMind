from django.shortcuts import redirect
from django.contrib import messages
from .models import Chat,Message
from django.shortcuts import get_object_or_404

def user_query_processing(request, chat_id):

    if request.method == "POST":
        message = request.POST.get("query_holder","").strip().lower()

        if not message:
            messages.error(request, "Query can't be empty!")
            return redirect("chatpage", chat_id)

        user_selected_docs=request.session.get("user_selected_docs")
        if not user_selected_docs:
            messages.error(request, "Please upload documents and select atleast one relevant document to query!")
            return redirect("chatpage", chat_id)

        chat = get_object_or_404(Chat, id=chat_id,user=request.user)

        Message.objects.create(
            chat=chat,
            role="user",
            message_text=message
        )

        if chat.chat_title == "New Chat":
            chat.chat_title = message[:60]
            chat.save()

        # Meghanath module call
        ai_response = "Hello"

        Message.objects.create(
            chat=chat,
            role="system",
            message_text=ai_response
        )

    return redirect("chatpage", chat_id)

