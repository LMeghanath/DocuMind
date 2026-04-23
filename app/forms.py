from django.contrib.auth.models import User
from django import forms
from .models import Document

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label="Confirm Password")

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")

        if password and password_confirm and password != password_confirm:
            raise forms.ValidationError("Passwords do not match!")
        return cleaned_data

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['file']
        
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file:
            raise forms.ValidationError("No document uploaded.")
        # Basic extension check matching util logic
        if not file.name.lower().endswith(('.pdf', '.txt')):
            raise forms.ValidationError("Only PDF and TXT files are supported.")
        return file
