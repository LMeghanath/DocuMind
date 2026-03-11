from django.shortcuts import render,redirect
from django.contrib import messages
from django.conf  import settings 
from django.contrib.auth.decorators import login_required
import os 
import uuid
from .models import Document,Profile,Chat
import hashlib
import shutil


@login_required
def select_docs(request):
    if request.method=="POST":
        docs=request.POST.getlist("selected_docs")
        request.session["user_selected_docs"]=docs
        """
        Session will be used by MEGHANATH to adjust context of prompt.
        """
    return redirect(request.META.get("HTTP_REFERER"))
    
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
                return redirect(request.META.get("HTTP_REFERER"))

            # MIME validation
            if doc.content_type != "application/pdf":
                messages.error(request, "Invalid file type. Please upload PDF files only!")
                return redirect(request.META.get("HTTP_REFERER"))

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
            display_name=os.path.basename(doc.name)
            display_name=display_name[:20]
            file_name = f"{uuid.uuid4()}.pdf"

            file_path = os.path.join(user_folder, file_name)

            with open(file_path, "wb+") as destination:
                for chunk in doc.chunks():
                    destination.write(chunk)

            document = Document(
                user=request.user,
                file_name=file_name,
                display_name=display_name,
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
        messages.success(request,"Uploaded Documents!")
        return redirect(request.META.get("HTTP_REFERER")) 

    return redirect(request.META.get("HTTP_REFERER"))        

def delete_all_docs(user):
    docs=Document.objects.filter(user=user)
    if not docs.exists():
        return False,"No documents have been uploaded by user to delete."    
    else:    
        """
            CALL ramaraju module to delete all indexes on this user.
        """
        size=0
        for doc in docs:
            if doc.file and os.path.exists(doc.file.path):
                os.remove(doc.file.path)
            
            size+=doc.file_size
            doc.delete()
        
        folder = os.path.join(settings.MEDIA_ROOT, "documents", str(user.id))
        if os.path.exists(folder):
            shutil.rmtree(folder)    
        
        user_profile=Profile.objects.get(user=user)
        user_profile.document_count=0
        user_profile.total_storage=max(0,user_profile.total_storage-size)
        user_profile.save()
        return True,"Deleted all files uploaded by user."    
                  
def delete_doc(request,id):
        user=request.user
        request.session.pop("user_selected_docs")
        try:
            doc=Document.objects.get(user=user,id=id)
        except Document.DoesNotExist:
            messages.error(request,"File not exists!")
            return redirect(request.META.get("HTTP_REFERER"))
         
        name=doc.display_name
        
        """
        CALL ramaraju module to reperform indexing on this user.
        """
        
        if os.path.exists(doc.file.path):
            os.remove(doc.file.path)
        
        size=doc.file_size
        doc.delete()
        user_profile=Profile.objects.get(user=user)
        user_profile.document_count-=1
        user_profile.total_storage=max(0,user_profile.total_storage-size)
        user_profile.save()
        messages.success(request,f"Deleted {name} file. ")
        return redirect(request.META.get("HTTP_REFERER"))
        