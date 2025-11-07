from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Add any additional fields specific to your application here.
    """
    # You can add custom fields here, for example:
    # phone_number = models.CharField(max_length=15, blank=True)
    # organization = models.CharField(max_length=255, blank=True)
    
    def __str__(self):
        return self.username
