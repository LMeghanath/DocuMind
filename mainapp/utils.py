"""
File contains functions that handle email_generation , hashing_otp , verifying_otp 
password_security_check
"""
from django.contrib import messages
from django.shortcuts import redirect
import secrets
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.hashers import make_password,check_password

def password_checking(request,password,repeat_password):
    length_flag=True
    password_match_flag=True
    if password!=repeat_password:
        password_match_flag=False
        messages.error(request,"Passwords don't match!")
    if len(password)<8:
        messages.error(request,"Password should have atleast eight(8) characters.")
        length_flag=False
    if len(password)>10:
        messages.error(request,"Password should not be have more than ten(10) characters.")
        length_flag=False
    small_flag=capital_flag=numeric_flag=special_char_flag=False
    
    for ch in password:
        if ord('A')<=ord(ch)<=ord('Z'):
            capital_flag=True
        elif ord('a')<=ord(ch)<=ord('z'):
            small_flag=True
        elif ord('0')<=ord(ch)<=ord('9'):
            numeric_flag=True
        else:
            special_char_flag=True

    if small_flag==False:
        messages.error(request,"Password should contain atleast one small letter.")
    if capital_flag==False:
        messages.error(request,"Password should contain atleast one capital letter.")
    if special_char_flag==False:
        messages.error(request,"Password should contain atleast one special character.")
    if numeric_flag==False:
        messages.error(request,"Password should contain atleast one digit.")
    return length_flag and numeric_flag and capital_flag and \
        small_flag and special_char_flag  and password_match_flag        

def send_otp(request,email):
    otp=generate_otp()
    subject="Verify Your Email - DocuMind"
    body=f"""
    Hello,

    Thank you for registering with DocuMind.

    Your One-Time Password (OTP) for email verification is:

    {otp}

    This OTP is valid for 10 minutes.

    If you did not request this, please ignore this email.

    Regards,
    DocuMind Team
    """
    try:
        send_custom_email(subject,body,email)
        request.session["hashed_otp"]=make_password(otp)
        return True
    except:
        return False    

def clear_sessions_signup(request):
    request.session.pop("signup_stage",None)
    request.session.pop("email",None)
    
def clear_sessions_password_reset(request):
    request.session.pop("reset_stage",None)
    request.session.pop("reset_email",None)
    

def verify_otp(request,otp):
    return check_password(otp,request.session.get("hashed_otp"))

def generate_otp():
    digits="0123456789"
    res=[]
    for _ in range(6):
        res.append(secrets.choice(digits))
    return "".join(res)    

def send_custom_email(subject, message, recipient_email): #can raise exception
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[recipient_email],
        fail_silently=False,
    )

               

