import logging
from django.db import models
from django.contrib.auth.models import User


logger = logging.getLogger(__name__)

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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    display_name = models.CharField(max_length=50, default="User Doc")
    file_name = models.CharField(max_length=255, null=True, blank=True)
    file_size = models.IntegerField(default=0)
    chunk_count = models.IntegerField(default=0)
    file = models.FileField(upload_to='documents/')
    file_hash = models.CharField(max_length=256, blank=True, null=True, db_index=True)
    is_processed = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    metadata_file_path = models.CharField(max_length=500, blank=True, null=True)

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error saving Document for user {self.user.username}: {str(e)}")
            raise e

    def __str__(self):
        return f"{self.display_name} (User: {self.user.username})"

class QueryLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='query_logs')
    query_text = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error saving QueryLog for user {self.user.username}: {str(e)}")
            raise e

    def __str__(self):
        return f"Query by {self.user.username} at {self.timestamp}"

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
