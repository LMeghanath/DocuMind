from django.shortcuts import render,redirect
from django.contrib.auth  import authenticate ,login,logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .utils import password_checking,verify_otp,send_otp

def homepage(request):
    return render(request,"mainapp/homepage.html")

@login_required
def chatpage(request):
    return render(request,"mainapp/chatpage.html")

def login_view(request):
    if request.user.is_authenticated==True:
        messages.error(request,"User already logged in.")
        return redirect("chatpage")

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
            return redirect("chatpage")
        else:
            messages.error(request,"Invalid credentials!")
            return redirect("login")
                    
    return render(request,"mainapp/login.html")    

@login_required
def logout_view(request):
    logout(request)
    return redirect("homepage")

def signup_view(request):
    if request.user.is_authenticated==True:
        messages.error(request,"User already logged in.")
        return redirect("chatpage")

    stage=request.session.get("signup_stage","email")

    if request.method=="POST":

        #------stage 1----------------------#
        if stage=="email":
            email=request.POST.get("email","")
            email=email.strip().lower()
            
            if not email:
                messages.error(request, "Email is required.")
                return redirect("signup_view")
            
            if User.objects.filter(email=email).exists():
                messages.error(request, "Email already registered.")
                return redirect("signup_view")

            request.session["email"]=email
            if send_otp(request,email): #also stores hashed otp in the session
                request.session["signup_stage"]="otp" 
            else:
                messages.error(request,"Failed to send OTP.")
            return redirect("signup_view")    
        #--------stage 2----------------------#
        elif stage=="otp":
            otp=request.POST.get("otp","")
            
            if not otp:
                messages.error(request, "OTP is required.")
                return redirect("signup_view")
            
            if verify_otp(request,otp):
                request.session.pop("org_hashed_otp", None)
                request.session["signup_stage"]="credentials"
            else:
                messages.error(request,"Invalid OTP.")
            return redirect("signup_view")    
        #--------stage 3----------------------#            
        else:
            username=request.POST.get("username","")
            username=username.strip().lower()

            if not username:
                messages.error(request, "Username is required.")
                return redirect("signup_view")
            
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already registered.")
                return redirect("signup_view")

            password=request.POST.get("password","")
            repeat_password=request.POST.get("repeat_password","")
            
            if not password or not repeat_password:
                messages.error(request, "Password fields are required.")
                return redirect("signup_view")
            email=request.session.get("email")
            if not email:
                messages.error(request, "Session expired. Please start again.")
                return redirect("signup_view")
            if password_checking(request,password,repeat_password):
                user=User.objects.create_user(
                    username=username,
                    email=email,
                    password=password
                )
                request.session.flush()
                login(request,user)
                return redirect("chatpage")
            else:
                return redirect("signup_view")
    return render(request,"mainapp/signup.html")

