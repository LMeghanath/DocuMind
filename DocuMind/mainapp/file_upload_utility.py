from django.shortcuts import redirect
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.decorators import login_required
import os
import uuid
import hashlib
import shutil
import logging
from django.db import transaction
from .models import Document, Profile, Chat
from .utils.validator import validate_file
from .utils.chunking import extract_and_chunk_file
from .utils.faiss_store import add_documents_to_store
from .utils.file_handler import get_user_lock

logger = logging.getLogger(__name__)

@login_required
def select_docs(request):
    if request.method == "POST":
        docs = request.POST.getlist("selected_docs")
        request.session["user_selected_docs"] = docs
    return redirect(request.META.get("HTTP_REFERER"))

@login_required
def upload_docs(request):
    if request.method == "POST":
        user_id = request.user.id
        user_folder = os.path.join(settings.DOCUMENT_ROOT, str(user_id))
        os.makedirs(user_folder, exist_ok=True)
        docs = request.FILES.getlist("documents")

        for doc in docs:
            if not doc.name.lower().endswith(".pdf"):
                messages.error(request, f"{doc.name}: Please upload PDF files only!")
                continue

            if doc.content_type != "application/pdf":
                messages.error(request, f"{doc.name}: Invalid file type!")
                continue

            hasher = hashlib.sha256()
            for chunk in doc.chunks():
                hasher.update(chunk)
            file_hash = hasher.hexdigest()

            if Document.objects.filter(user=request.user, file_hash=file_hash).exists():
                messages.error(request, f"Duplicate document detected - {doc.name}.")
                continue

            doc.seek(0)
            
            lock = get_user_lock(request.user.id)
            with lock:
                is_valid, msg, _ = validate_file(doc, request.user)
                if not is_valid:
                    messages.error(request, f"{doc.name}: {msg}")
                    continue

                display_name = os.path.basename(doc.name)[:45]
                file_name = f"{uuid.uuid4()}.pdf"
                file_path = os.path.join(user_folder, file_name)

                with open(file_path, "wb+") as destination:
                    for chunk in doc.chunks():
                        destination.write(chunk)

                with transaction.atomic():
                    document = Document(
                        user=request.user,
                        file_name=file_name,
                        display_name=display_name,
                        file_size=doc.size,
                        chunk_count=0,
                        file=f"documents/{user_id}/{file_name}",
                        file_hash=file_hash,
                        is_processed=False
                    )
                    document.save()
                    
                    try:
                        chunks = extract_and_chunk_file(document.file.path)
                        add_documents_to_store(request.user.id, document.id, chunks)
                        document.is_processed = True
                        document.chunk_count = len(chunks)
                        document.save()

                        profile, _ = Profile.objects.get_or_create(user=request.user, defaults={'email': request.user.email})
                        profile.document_count += 1
                        profile.total_storage += doc.size
                        profile.save()
                        messages.success(request, f"Uploaded and indexed {doc.name} successfully!")

                    except Exception as e:
                        logger.error(f"Error indexing {doc.name}: {e}")
                        messages.error(request, f"Error indexing {doc.name}: {e}")

    return redirect(request.META.get("HTTP_REFERER"))

def delete_all_docs(user):
    docs = Document.objects.filter(user=user)
    if not docs.exists():
        return False, "No documents have been uploaded."

    size = 0
    for doc in docs:
        if doc.file and os.path.exists(doc.file.path):
            os.remove(doc.file.path)
        size += doc.file_size
        doc.delete()

    folder = os.path.join(settings.DOCUMENT_ROOT, str(user.id))
    if os.path.exists(folder):
        shutil.rmtree(folder)

    index_root = os.path.join(settings.INDEX_ROOT, str(user.id))
    if os.path.exists(index_root):
        shutil.rmtree(index_root)

    try:
        user_profile = Profile.objects.get(user=user)
        user_profile.document_count = 0
        user_profile.total_storage = max(0, user_profile.total_storage - size)
        user_profile.save()
    except Profile.DoesNotExist:
        pass

    return True, "Deleted all files uploaded by user."

def delete_doc(request, id):
    user = request.user
    if "user_selected_docs" in request.session:
        request.session.pop("user_selected_docs")

    try:
        doc = Document.objects.get(user=user, id=id)
    except Document.DoesNotExist:
        messages.error(request, "File not exists!")
        return redirect(request.META.get("HTTP_REFERER"))

    name = doc.display_name
    
    doc_store_dir = os.path.join(settings.INDEX_ROOT, str(request.user.id), str(doc.id))
    if os.path.exists(doc_store_dir):
        try:
            shutil.rmtree(doc_store_dir)
        except Exception:
            pass

    if doc.file and os.path.exists(doc.file.path):
        os.remove(doc.file.path)

    size = doc.file_size
    doc.delete()

    try:
        user_profile = Profile.objects.get(user=user)
        user_profile.document_count -= 1
        user_profile.total_storage = max(0, user_profile.total_storage - size)
        user_profile.save()
    except Profile.DoesNotExist:
        pass

    messages.success(request, f"Deleted {name} file.")
    return redirect(request.META.get("HTTP_REFERER"))
