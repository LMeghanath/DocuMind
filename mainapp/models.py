from django.db import models
from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator

class Profile(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    email=models.EmailField(unique=True)
    document_count=models.IntegerField(default=0)
    api_usage=models.IntegerField(default=0)
    total_storage=models.BigIntegerField(default=0)
    subscription_type=models.CharField(max_length=20,default="Free")
    
    def __str__(self):
        return f"{self.user.username} Profile" 

class Document(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    file_name=models.CharField(max_length=255) #internal unique name 
    display_name=models.CharField(max_length=50,default="User Doc") #display name for user
    file=models.FileField(upload_to='user_documents/',
                          validators=[FileExtensionValidator(allowed_extensions=["pdf"])])
    file_size=models.IntegerField()
    chunk_count=models.IntegerField()
    file_hash=models.CharField(max_length=64)
    upload_time=models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together=("user","file_hash")

class Chat(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    chat_time=models.DateTimeField(auto_now_add=True)
    chat_title=models.CharField(max_length=200,default="New Chat")
    class Meta:
        ordering=["-chat_time"]

class Message(models.Model):
    ROLES=[
        ("user","User"),
        ("assistant","Assistant"),
        ("system","System"),
    ]

    chat=models.ForeignKey(Chat,on_delete=models.CASCADE,related_name = "messages")
    role=models.CharField(max_length=10,choices=ROLES)
    message_text=models.TextField()
    message_time=models.DateTimeField(auto_now_add=True)

class Chunk(models.Model):
    document=models.ForeignKey(Document,on_delete=models.CASCADE)
    chunk_text=models.TextField()
    chunk_index=models.IntegerField()  
    faiss_index=models.IntegerField(unique=True)
    page_number=models.IntegerField()
    class Meta:
        unique_together=("document","chunk_index")  

