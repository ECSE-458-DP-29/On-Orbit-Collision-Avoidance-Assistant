from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    
    Roles:
    - ADMIN: Full access including admin panel (use createsuperuser)
    - WORKER: Can view/add/edit/delete CDMs, view globe, no admin panel
    - OBSERVER: Read-only access to CDMs and globe (default for new users)
    """
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('worker', 'Worker'),
        ('observer', 'Observer'),
    ]
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='observer',
        help_text="User role determining access permissions"
    )
    
    def __str__(self):
        return self.username
    
    def save(self, *args, **kwargs):
        """Auto-set role to admin for superusers."""
        if self.is_superuser:
            self.role = 'admin'
        super().save(*args, **kwargs)
    
    def can_modify_cdm(self):
        """Check if user can create/edit/delete CDMs."""
        return self.role in ['admin', 'worker'] or self.is_superuser
    
    def can_access_admin(self):
        """Check if user can access admin panel."""
        return self.role == 'admin' or self.is_superuser
