from django.db import models


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
