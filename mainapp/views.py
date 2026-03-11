from django.shortcuts import render,redirect
from django.contrib.auth  import authenticate ,login,logout
from django.contrib.auth.models import User
from .models import Profile,Document,Chat
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .file_upload_utility import delete_doc,delete_all_docs
from .utils import password_checking,verify_otp,send_otp,clear_sessions_signup,clear_sessions_password_reset
import os 
from django.db.models import Count

"""
IMP
clear_sessions_signup() and clear_sessions_password_reset() - user defined function to clear residual sessions of signup_view 
used to carry out a multi stage form for user registration.
It will not affect sessions related to user-object which is used to check login status , etc. 
"""
def homepage(request):
    clear_sessions_signup(request)
    clear_sessions_password_reset(request)
    return render(request,"mainapp/homepage.html")

@login_required
def delete_doc_view(request,id):
    return delete_doc(request,id)

@login_required
def delete_all_docs_view(request):
    flag,message=delete_all_docs(request.user)
    if flag==True:
        messages.success(request,message)
    else:
        messages.error(request,message)    
    return redirect(request.META.get("HTTP_REFERER"))

@login_required
def new_chat_view(request):
    Chat.objects.filter(user=request.user)\
        .annotate(msg_count=Count("messages"))\
        .filter(msg_count=0)\
        .delete()
    chat=Chat(user=request.user,)
    chat.save()
    return redirect("chatpage",chat.id)
     
@login_required
def chatpage_view(request,chat_id):
    context={}
    docs=Document.objects.filter(user=request.user)
    chat=Chat.objects.filter(user=request.user).order_by("-chat_time")
    context["docs"]=docs
    clear_sessions_signup(request)
    clear_sessions_password_reset(request)
    return render(request,"mainapp/chatpage.html",context)

def login_view(request):
    clear_sessions_signup(request)
    clear_sessions_password_reset(request)
    if request.user.is_authenticated==True:
        messages.error(request,"User already logged in.")
        return redirect(request.META.get("HTTP_REFERER"))

    if request.method=="POST":
        email=request.POST.get("email","").strip().lower()
        password=request.POST.get("password")

        try:
            user=User.objects.get(email=email)
            user=authenticate(request,username=user.username,password=password)
        except User.DoesNotExist:
            user=None 

        if user!=None:
            login(request,user)
            return redirect("new_chat")
        else:
            messages.error(request,"Invalid credentials!")
            return redirect("login")
                    
    return render(request,"mainapp/login.html")    

@login_required
def logout_view(request):
    clear_sessions_signup(request)
    clear_sessions_password_reset(request)
    logout(request)
    return redirect("homepage")


def signup_view(request):
    clear_sessions_password_reset(request)
    
    if request.user.is_authenticated==True:
        messages.error(request,"User already logged in.")
        return redirect(request.META.get("HTTP_REFERER"))

    stage=request.session.get("signup_stage","email")

    if request.method=="POST":

        #------stage 1----------------------#
        if stage=="email":
            email=request.POST.get("email","")
            email=email.strip().lower()
            
            if not email:
                messages.error(request, "Email is required.")
                return redirect("signup")
            
            if User.objects.filter(email=email).exists():
                messages.error(request, "An account exists with this email.Try login instead.")
                return redirect("signup")

            request.session["email"]=email
            if send_otp(request,email): #also stores hashed otp in the session
                request.session["signup_stage"]="otp" 
            else:
                messages.error(request,"Failed to send OTP.")
            return redirect("signup")    
        #--------stage 2----------------------#
        elif stage=="otp":
            otp=request.POST.get("otp","")
            
            if not otp:
                messages.error(request, "OTP is required.")
                return redirect("signup")
            
            if verify_otp(request,otp):
                request.session.pop("hashed_otp", None)
                request.session["signup_stage"]="credentials"
            else:
                messages.error(request,"Invalid OTP.")
            return redirect("signup")    
        #--------stage 3----------------------#            
        else:
            username=request.POST.get("username","")
            username=username.strip().lower()

            if not username:
                messages.error(request, "Username is required.")
                return redirect("signup")
            
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already registered.Try a different username.")
                return redirect("signup")

            password=request.POST.get("password","")
            repeat_password=request.POST.get("repeat_password","")
            
            if not password or not repeat_password:
                messages.error(request, "Password fields are required.")
                return redirect("signup")
            email=request.session.get("email")
            if not email:
                messages.error(request, "Session expired. Please start again.")
                return redirect("signup")
            if password_checking(request,password,repeat_password):
                user=User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                Profile.objects.create(user=user, email=email)
                request.session.flush()
                login(request,user)
                return redirect("new_chat")
            else:
                return redirect("signup")
    
    return render(request,"mainapp/signup.html")

@login_required
def profile_view(request):
    clear_sessions_signup(request)
    clear_sessions_password_reset(request)
    return render(request,"mainapp/profile.html")

@login_required
def delete_account_view(request):
    clear_sessions_signup(request)
    clear_sessions_password_reset(request)
    user=request.user
    flag,message=delete_all_docs(user)
    if flag==True:
        messages.success(request,message)
    else:
        messages.error(request,message)    
    user.delete()
    request.session.flush()
    messages.success(request,"Account has been successfully deleted.")
    return redirect("homepage")

def password_reset_view(request):
    clear_sessions_signup(request)
    
    stage=request.session.get("reset_stage","email")

    if request.method=="POST":
        
        if stage=="email":
            #-------------stage 1--------------#
            email=request.POST.get("email")
            email=email.strip().lower()

            if not email:
                messages.error(request,"Email field is mandatory!")
                return redirect("password_reset")
            
            user=User.objects.filter(email=email)

            if user:
                request.session["reset_email"]=email
                if send_otp(request,email): #also stores hashed otp in the session
                    request.session["reset_stage"]="otp" 
                else:
                    messages.error(request,"Failed to send OTP.")
                    return redirect("password_reset")
            else:
                messages.error(request,"Please enter a registered mail id.")
                return redirect("password_reset")
        
        elif stage=="otp":

            #-------------stage 2--------------#
            otp=request.POST.get("otp")
            otp=otp.strip()

            if not otp:
                messages.error(request,"OTP field is mandatory!")
                return redirect("password_reset")
            
            if verify_otp(request,otp):
                request.session.pop("hashed_otp",None)
                request.session["reset_stage"]="credentials"
            else:
                messages.error(request,"Please enter a valid otp.")
                return redirect("password_reset")
        else:
            #-------------stage 3--------------#
            password=request.POST.get("password","")
            repeat_password=request.POST.get("repeat_password","")
            
            if not password or not repeat_password:
                messages.error(request, "Password fields are required.")
                return redirect("password_reset")
            
            email=request.session.get("reset_email")
            if not email:
                messages.error(request, "Session expired. Please start again.")
                return redirect("password_reset")
            
            if password_checking(request,password,repeat_password):
                user=User.objects.get(email=email)
                user.set_password(password)
                user.save()
                request.session.flush()
                messages.success(request,"Password has been successfully reset. \n Please login.")
                return redirect("login")
            else:
                return redirect("password_reset")

    return render(request,"mainapp/password_reset.html")    
            