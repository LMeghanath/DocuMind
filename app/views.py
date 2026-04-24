"""
This file contains code for handling user account:

Create account 
Deleting account
Password reset
Login 
Signup

"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from .models import Profile, Document, Chat, Message
from .file_upload_utility import delete_doc, delete_all_docs
from .utils.auth_utils import password_checking, verify_otp, send_otp, clear_sessions_signup, clear_sessions_password_reset

def homepage(request):
    clear_sessions_signup(request)
    clear_sessions_password_reset(request)
    return render(request, "app/homepage.html")

@login_required
def delete_doc_view(request, id):
    return delete_doc(request, id)

@login_required
def delete_all_docs_view(request):
    flag, message = delete_all_docs(request.user)
    request.session.pop("user_selected_docs", None)
    if flag:
        messages.success(request, message)
    else:
        messages.error(request, message)    
    return redirect(request.META.get("HTTP_REFERER", "homepage"))

@login_required
def new_chat_view(request):
    Chat.objects.filter(user=request.user)\
        .annotate(msg_count=Count("messages"))\
        .filter(msg_count=0)\
        .delete()
    chat = Chat(user=request.user)
    chat.save()
    return redirect("chatpage", chat.id)
     
@login_required
def chatpage_view(request, chat_id):
    clear_sessions_signup(request)
    clear_sessions_password_reset(request)
    
    context = {}
    user_docs = Document.objects.filter(user=request.user)
    
    chat = get_object_or_404(Chat, id=chat_id, user=request.user)
    chat_messages = Message.objects.filter(chat=chat)
    
    chats = Chat.objects.filter(user=request.user).order_by("-chat_time")
    context["docs"] = user_docs
    context["chat_messages"] = chat_messages
    context["chats"] = chats
    context["chat"] = chat
    return render(request, "app/chatpage.html", context)

def login_view(request):
    clear_sessions_signup(request)
    clear_sessions_password_reset(request)
    if request.user.is_authenticated:
        messages.error(request, "User already logged in.")
        return redirect(request.META.get("HTTP_REFERER", "homepage"))

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password")

        try:
            user = User.objects.get(email=email)
            user = authenticate(request, username=user.username, password=password)
        except User.DoesNotExist:
            user = None 

        if user is not None:
            login(request, user)
            return redirect("new_chat")
        else:
            messages.error(request, "Invalid credentials!")
            return redirect("login")
                    
    return render(request, "app/login.html")    

@login_required
def logout_view(request):
    clear_sessions_signup(request)
    clear_sessions_password_reset(request)
    logout(request)
    return redirect("homepage")

def signup_view(request):
    clear_sessions_password_reset(request)
    if request.user.is_authenticated:
        messages.error(request, "User already logged in.")
        return redirect(request.META.get("HTTP_REFERER", "homepage"))

    stage = request.session.get("signup_stage", "email")

    if request.method == "POST":
        if stage == "email":
            email = request.POST.get("email", "").strip().lower()
            if not email:
                messages.error(request, "Email is required.")
                return redirect("signup")
            
            if User.objects.filter(email=email).exists():
                messages.error(request, "An account exists with this email. Try login instead.")
                return redirect("signup")

            request.session["email"] = email
            if send_otp(request, email):
                request.session["signup_stage"] = "otp" 
            else:
                messages.error(request, "Failed to send OTP.")
            return redirect("signup")    
            
        elif stage == "otp":
            otp = request.POST.get("otp", "")
            if not otp:
                messages.error(request, "OTP is required.")
                return redirect("signup")
            
            if verify_otp(request, otp):
                request.session.pop("hashed_otp", None)
                request.session["signup_stage"] = "credentials"
            else:
                messages.error(request, "Invalid OTP.")
            return redirect("signup")    
            
        else:
            username = request.POST.get("username", "").strip().lower()
            if not username:
                messages.error(request, "Username is required.")
                return redirect("signup")
            
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already registered. Try a different username.")
                return redirect("signup")

            password = request.POST.get("password", "")
            repeat_password = request.POST.get("repeat_password", "")
            
            if not password or not repeat_password:
                messages.error(request, "Password fields are required.")
                return redirect("signup")
                
            email = request.session.get("email")
            if not email:
                messages.error(request, "Session expired. Please start again.")
                return redirect("signup")
                
            if password_checking(request, password, repeat_password):
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                Profile.objects.create(user=user, email=email)
                request.session.flush()
                login(request, user)
                return redirect("new_chat")
            else:
                return redirect("signup")
    
    return render(request, "app/signup.html")

@login_required
def profile_view(request):
    clear_sessions_signup(request)
    clear_sessions_password_reset(request)
    return render(request, "app/profile.html")

@login_required
def delete_account_view(request):
    clear_sessions_signup(request)
    clear_sessions_password_reset(request)
    user = request.user
    flag, message = delete_all_docs(user)
    if flag:
        messages.success(request, message)
    else:
        messages.error(request, message)    
    user.delete()
    request.session.flush()
    messages.success(request, "Account has been successfully deleted.")
    return redirect("homepage")

def password_reset_view(request):
    clear_sessions_signup(request)
    stage = request.session.get("reset_stage", "email")

    if request.method == "POST":
        if stage == "email":
            email = request.POST.get("email", "").strip().lower()
            if not email:
                messages.error(request, "Email field is mandatory!")
                return redirect("password_reset")
            
            user = User.objects.filter(email=email).first()
            if user:
                request.session["reset_email"] = email
                if send_otp(request, email):
                    request.session["reset_stage"] = "otp" 
                else:
                    messages.error(request, "Failed to send OTP.")
                    return redirect("password_reset")
            else:
                messages.error(request, "Please enter a registered mail id.")
                return redirect("password_reset")
        
        elif stage == "otp":
            otp = request.POST.get("otp", "").strip()
            if not otp:
                messages.error(request, "OTP field is mandatory!")
                return redirect("password_reset")
            
            if verify_otp(request, otp):
                request.session.pop("hashed_otp", None)
                request.session["reset_stage"] = "credentials"
            else:
                messages.error(request, "Please enter a valid otp.")
                return redirect("password_reset")
        else:
            password = request.POST.get("password", "")
            repeat_password = request.POST.get("repeat_password", "")
            
            if not password or not repeat_password:
                messages.error(request, "Password fields are required.")
                return redirect("password_reset")
            
            email = request.session.get("reset_email")
            if not email:
                messages.error(request, "Session expired. Please start again.")
                return redirect("password_reset")
            
            if password_checking(request, password, repeat_password):
                user = User.objects.get(email=email)
                user.set_password(password)
                user.save()
                request.session.flush()
                messages.success(request, "Password has been successfully reset. \n Please login.")
                return redirect("login")
            else:
                return redirect("password_reset")

    return render(request, "app/password_reset.html")
