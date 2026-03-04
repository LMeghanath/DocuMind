from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    email=models.EmailField(unique=True)
    document_count=models.IntegerField(default=0)
    api_usage=models.IntegerField(default=0)
    total_storage=models.BigIntegerField(default=0)
    subscription_type=models.CharField(max_length=20,default="Free")
    
    def __str__(self):
        return f"{self.user.name} Profile" 

