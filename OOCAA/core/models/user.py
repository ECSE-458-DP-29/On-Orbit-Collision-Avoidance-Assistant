from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom User with role support."""

    class Role(models.TextChoices):
        ADMIN = "admin", "Admin"
        OPERATOR = "operator", "Operator"
        OBSERVER = "observer", "Observer"

    # make sure emails are unique
    email = models.EmailField(unique=True)

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.OBSERVER,
    )

    def __str__(self):
        return f"{self.username} ({self.role})"

    def save(self, *args, **kwargs):
        # Defensive: if someone sets a plain password directly, hash it.
        if self.password and '$' not in self.password:
            self.set_password(self.password)
        super().save(*args, **kwargs)

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_operator(self):
        return self.role == self.Role.OPERATOR

    @property
    def is_observer(self):
        return self.role == self.Role.OBSERVER
