from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


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
    

class SpaceObject(models.Model):
    """
    Model representing a space object involved in collision avoidance.
    """
    class ObjectType(models.TextChoices):
        PAYLOAD     = "PAYLOAD", "PAYLOAD" # The first value is stored in DB, the second is human-readable
        ROCKET_BODY = "ROCKET BODY", "ROCKET BODY"
        DEBRIS      = "DEBRIS", "DEBRIS"
        UNKNOWN     = "UNKNOWN", "UNKNOWN"
        OTHER       = "OTHER", "OTHER"

    object_designator = models.CharField(max_length=32, unique=True)   
    object_name = models.CharField(max_length=128)                     
    object_type = models.CharField(
        max_length=12,  # long enough for "ROCKET BODY"
        choices=ObjectType.choices,
        default=ObjectType.UNKNOWN,
    )  
    operator_organization = models.CharField(max_length=128)           
    maneuverable = models.BooleanField()                               

    def __str__(self):
        return f"{self.object_designator} ({self.object_name})"


class CDM(models.Model):
    """Model representing a Conjunction Data Message (CDM)."""
    # Auto-increment integer primary key added automatically as `id`

    obj1 = models.ForeignKey(
        SpaceObject,
        related_name='cdms_as_obj1',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    obj2 = models.ForeignKey(
        SpaceObject,
        related_name='cdms_as_obj2',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    tca = models.DateTimeField()                                        
    miss_distance_m = models.FloatField(null=True, blank=True)  
    relative_position_r = models.FloatField(null=True, blank=True)
    relative_position_t = models.FloatField(null=True, blank=True)
    relative_position_n = models.FloatField(null=True, blank=True)

    collision_probability = models.DecimalField(
        max_digits=20,
        decimal_places=12,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(1)],
    )

    collision_probability_method = models.CharField(
        max_length=32, default="OTHER"
    )

    def __str__(self):
        return f"CDM #{self.id} @ {self.tca.isoformat()}"
