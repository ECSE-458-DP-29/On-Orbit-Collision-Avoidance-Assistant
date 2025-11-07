from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from .spaceobject import SpaceObject


class CDM(models.Model):
    """Model representing a Conjunction Data Message (CDM)."""

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
