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

    event = models.ForeignKey(
        'Event',
        related_name='cdms',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )

    # Object 1 State Vector (ECI frame)
    obj1_position_x = models.FloatField(
        null=True,
        blank=True,
        help_text="Object 1 X position in ECI frame (meters)"
    )
    obj1_position_y = models.FloatField(
        null=True,
        blank=True,
        help_text="Object 1 Y position in ECI frame (meters)"
    )
    obj1_position_z = models.FloatField(
        null=True,
        blank=True,
        help_text="Object 1 Z position in ECI frame (meters)"
    )
    obj1_velocity_x = models.FloatField(
        null=True,
        blank=True,
        help_text="Object 1 X velocity in ECI frame (m/s)"
    )
    obj1_velocity_y = models.FloatField(
        null=True,
        blank=True,
        help_text="Object 1 Y velocity in ECI frame (m/s)"
    )
    obj1_velocity_z = models.FloatField(
        null=True,
        blank=True,
        help_text="Object 1 Z velocity in ECI frame (m/s)"
    )

    # Object 2 State Vector (ECI frame)
    obj2_position_x = models.FloatField(
        null=True,
        blank=True,
        help_text="Object 2 X position in ECI frame (meters)"
    )
    obj2_position_y = models.FloatField(
        null=True,
        blank=True,
        help_text="Object 2 Y position in ECI frame (meters)"
    )
    obj2_position_z = models.FloatField(
        null=True,
        blank=True,
        help_text="Object 2 Z position in ECI frame (meters)"
    )
    obj2_velocity_x = models.FloatField(
        null=True,
        blank=True,
        help_text="Object 2 X velocity in ECI frame (m/s)"
    )
    obj2_velocity_y = models.FloatField(
        null=True,
        blank=True,
        help_text="Object 2 Y velocity in ECI frame (m/s)"
    )
    obj2_velocity_z = models.FloatField(
        null=True,
        blank=True,
        help_text="Object 2 Z velocity in ECI frame (m/s)"
    )

    # Covariance Matrices (ECI frame, 6x6 stored as JSON)
    obj1_covariance_matrix = models.JSONField(
        null=True,
        blank=True,
        help_text="Object 1 6x6 covariance matrix in ECI frame (m^2, m^2/s, nested array)"
    )
    obj2_covariance_matrix = models.JSONField(
        null=True,
        blank=True,
        help_text="Object 2 6x6 covariance matrix in ECI frame (m^2, m^2/s, nested array)"
    )

    # Hard Body Radius
    hard_body_radius = models.FloatField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
        help_text="Combined hard body radius (meters)"
    )

    def __str__(self):
        return f"CDM #{self.id} @ {self.tca.isoformat()}"
