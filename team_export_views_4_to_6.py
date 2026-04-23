"""
================================================================================
TEAM EXPORT: Django Views for Modules 4, 5, and 6
================================================================================
This file demonstrates how the Preprocessing, extraction, chunking, and FAISS
storage (Modules 4, 5, 6) are integrated into a Django view pipeline.

Your team can use this as a reference for handling the file parsing and vector
storage after the user uploads it. To use this code, ensure you have imported 
the utility logic we provided in `team_export_modules_4_to_6.py`.
================================================================================
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Document
from .forms import DocumentUploadForm

# Import the consolidated utilities from the team export file
# (Replace these imports with wherever your team places the functions)
# from .utils.chunking import extract_and_chunk_file
# from .utils.faiss_store import add_documents_to_store

@login_required
def upload_and_process_document(request):
    """
    View that handles file upload (Module 3) and triggers 
    Preprocessing (Module 4), Chunking (Module 5), and FAISS Embeddings (Module 6).
    """
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            
            # --- START INTEGRATION POINT FOR MODULES 4, 5, 6 ---
            try:
                # [Module 3: File Upload] 
                # After passing your upload validation (e.g. hash checks, locking),
                # Save the document to the database temporarily to retrieve its OS path
                document = form.save(commit=False)
                document.user = request.user
                document.save()
                
                # [Module 4 & 5: Preprocessing, Extraction + Chunking]
                # Pass the absolute file path of the saved document to the chunker.
                # The extract_and_chunk_file utility uses Langchain loaders to read the file,
                # then calls preprocess_text() on the contents, and splits them recursively.
                chunks = extract_and_chunk_file(document.file.path)
                
                # [Module 6: Embeddings + FAISS Storage]
                # Pass the user's ID and the extracted chunks to the storage engine.
                # This will initialize Gemini embeddings, add the chunks to the FAISS 
                # vector store, generate the JSON metadata, and save them atomically.
                add_documents_to_store(request.user.id, chunks)
                
                # If everything succeeded, notify the user.
                messages.success(request, f"Document '{document.file.name}' processed and embedded successfully!")
                return redirect('app:dashboard')
                
            except Exception as e:
                # Basic try-catch error handling to prevent 500 crashes
                messages.error(request, f"An error occurred during AI processing: {str(e)}")
                return redirect('app:dashboard')
            # --- END INTEGRATION POINT ---
            
    else:
        form = DocumentUploadForm()
        
    return render(request, 'app/upload.html', {'form': form})
