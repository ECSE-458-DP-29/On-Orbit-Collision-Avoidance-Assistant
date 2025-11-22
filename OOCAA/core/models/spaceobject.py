from django.db import models


class SpaceObject(models.Model):
    """
    Model representing a space object involved in collision avoidance.
    """
    object_designator = models.CharField(max_length=32, unique=True)
    object_name = models.CharField(max_length=128, null=True, blank=True)
    object_type = models.CharField(max_length=64, null=True, blank=True)
    operator_organization = models.CharField(max_length=128, null=True, blank=True)
    maneuverable = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.object_designator} ({self.object_name})"
