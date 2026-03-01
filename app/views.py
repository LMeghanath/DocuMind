from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from .forms import UserRegistrationForm

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
    return render(request, 'app/dashboard.html')
