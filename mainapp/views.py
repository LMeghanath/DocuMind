from django.shortcuts import render,redirect
from django.contrib.auth  import authenticate,login
from django.contrib.auth.decorators import login_required
from django.contrib import messages

def homepage(request):
    return render(request,"mainapp/homepage.html")

@login_required
def chatpage(request):
    return render(request,"mainapp/chatpage.html")

def login(request):
    if request.method=="POST":
        email=request.POST.get("email")
        password=request.POST.get("password")

        try:
            user=user.objects.get(email=email)
            user=authenticate(request,user.username,password)
        except user.DoesNotExist:
            user=None
            messages.error("Invalid credentials!")    

        if user!=None:
            login(request,user)
            redirect("chatpage")
                    
    return render(request,"mainapp/login.html")    

@login_required
def logout(request):
    logout(request)
    redirect("homepage")
