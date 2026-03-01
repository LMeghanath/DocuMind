import logging
from django.db import models
from django.contrib.auth.models import User

logger = logging.getLogger(__name__)

class Document(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='documents')
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    metadata_file_path = models.CharField(max_length=500, blank=True, null=True)

    def save(self, *args, **kwargs):
        try:
            super().save(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error saving Document for user {self.user.username}: {str(e)}")
            raise e

    def __str__(self):
        return f"{self.file.name} (User: {self.user.username})"

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
