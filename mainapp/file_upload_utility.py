from django.shortcuts import render,redirect
from django.contrib import messages
from django.conf  import settings 
from django.contrib.auth.decorators import login_required
import os 
import uuid
from .models import Document,Profile
import hashlib

@login_required
def upload_docs(request):

    if request.method == "POST":

        user_id = request.user.id

        user_folder = os.path.join(
            settings.MEDIA_ROOT,
            "documents",
            str(user_id)
        )

        os.makedirs(user_folder, exist_ok=True)

        docs = request.FILES.getlist("documents")

        for doc in docs:

            # extension validation
            if not doc.name.lower().endswith(".pdf"):
                messages.error(request, "Please upload PDF files only!")
                return redirect("chatpage")

            # MIME validation
            if doc.content_type != "application/pdf":
                messages.error(request, "Invalid file type. Please upload PDF files only!")
                return redirect("chatpage")

            """
            Run RAMARAJU module checker here
            """

            # Generate file hash
            hasher = hashlib.sha256()

            for chunk in doc.chunks():
                hasher.update(chunk)

            file_hash = hasher.hexdigest()

            # Prevent duplicate uploads
            if Document.objects.filter(user=request.user, file_hash=file_hash).exists():
                messages.error(request, f"Duplicate document detected - {doc.name}.")
                continue

            # Reset pointer
            doc.seek(0)

            file_name = f"{uuid.uuid4()}.pdf"

            file_path = os.path.join(user_folder, file_name)

            with open(file_path, "wb+") as destination:
                for chunk in doc.chunks():
                    destination.write(chunk)

            document = Document(
                user=request.user,
                file_name=file_name,
                file_size=doc.size,
                chunk_count=0,
                file=f"documents/{user_id}/{file_name}",
                file_hash=file_hash
            )

            document.save()

            profile = request.user.profile

            profile.document_count += 1
            profile.total_storage += doc.size
            profile.save()

    return render(request,"mainapp/chatpage.html")        