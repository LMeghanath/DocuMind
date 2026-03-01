from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, DocumentUploadForm
from .models import Document
from .utils.file_handler import handle_uploaded_file, get_user_lock, calculate_file_hash

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            login(request, user)
            return redirect('app:dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'app/register.html', {'form': form})

@login_required
def dashboard(request):
    documents = Document.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'app/dashboard.html', {'documents': documents})

@login_required
def upload_document(request):
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            
            # 1. basic try/catch
            try:
                # 2. Acquire user-specific lock to prevent race conditions during parallel uploads
                lock = get_user_lock(request.user.id)
                with lock:
                    # 3. Handle file edge cases using utility
                    is_valid, msg = handle_uploaded_file(uploaded_file, request.user.id)
                    if not is_valid:
                        messages.error(request, msg)
                        return redirect('app:upload')

                    # Calculate hash to detect duplicate
                    uploaded_file.seek(0)
                    file_hash = calculate_file_hash(uploaded_file.read())
                    uploaded_file.seek(0) # reset
                    
                    # Check duplicate in DB (Assuming identical files not allowed per user)
                    # We can store file_hash in Document model if we add a field, or compare filenames 
                    # For simple minor project: we check if user already has a file with this name
                    if Document.objects.filter(user=request.user, file__endswith=uploaded_file.name).exists():
                        messages.error(request, "A document with this name already exists (Duplicate).")
                        return redirect('app:upload')

                    # 4. Save to DB
                    document = form.save(commit=False)
                    document.user = request.user
                    document.save()
                    
                    messages.success(request, f"Document '{document.file.name}' uploaded successfully!")
                    return redirect('app:dashboard')
                    
            except Exception as e:
                messages.error(request, f"An error occurred during upload: {str(e)}")
                return redirect('app:upload')
    else:
        form = DocumentUploadForm()
        
    return render(request, 'app/upload.html', {'form': form})

