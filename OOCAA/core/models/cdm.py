from django.db import models
from .spaceobject import SpaceObject


class CDM(models.Model):
    """
    Model representing a Conjunction Data Message (CDM).
    """

    # Metadata
    cdm_id = models.CharField(max_length=64, null=True, blank=True)
    message_id = models.CharField(max_length=128, null=True, blank=True)
    creation_date = models.DateTimeField(null=True, blank=True)
    insert_epoch = models.DateTimeField(null=True, blank=True)
    ccsds_version = models.CharField(max_length=16, null=True, blank=True)
    originator = models.CharField(max_length=128, null=True, blank=True)

    # Space objects involved in the conjunction
    obj1 = models.ForeignKey(
        SpaceObject, related_name="cdms_as_obj1", null=True, blank=True, on_delete=models.SET_NULL
    )
    obj2 = models.ForeignKey(
        SpaceObject, related_name="cdms_as_obj2", null=True, blank=True, on_delete=models.SET_NULL
    )

    # State vectors and physical parameters for obj1 and obj2
    state_vector_obj1 = models.JSONField(null=True, blank=True)  # x, y, z, xdot, ydot, zdot
    state_vector_obj2 = models.JSONField(null=True, blank=True)  # x, y, z, xdot, ydot, zdot
    physical_parameters_obj1 = models.JSONField(null=True, blank=True)  # area_pc, cd_area_mass, etc.
    physical_parameters_obj2 = models.JSONField(null=True, blank=True)  # area_pc, cd_area_mass, etc.

    # Encounter geometry
    tca = models.DateTimeField()  # Time of closest approach
    miss_distance_m = models.FloatField(null=True, blank=True)
    relative_speed_ms = models.FloatField(null=True, blank=True)

    # Relative position and velocity (RTN)
    relative_position = models.JSONField(null=True, blank=True)  # r, t, n
    relative_velocity = models.JSONField(null=True, blank=True)  # r, t, n

    # Collision probability
    collision_probability = models.DecimalField(
        max_digits=20, decimal_places=12, null=True, blank=True
    )
    collision_probability_method = models.CharField(max_length=64, null=True, blank=True)

    # Additional comments or metadata
    comments = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"CDM {self.cdm_id} @ {self.tca}"
