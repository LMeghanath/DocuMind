"""
File contains functions that handle email_generation , hashing_otp , verifying_otp 
password_security_check
"""
from django.contrib import messages

def password_checking(request,password,repeat_password):
    length_flag=True
    if password!=repeat_password:
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
        small_flag and special_char_flag         

def send_otp(request,email):
    pass

def verify_otp(request,otp):
    pass

def hash_otp(otp):
    pass


               

