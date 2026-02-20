from django.db import models
from django.core.validators import MinValueValidator
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
    
    # Event grouping
    event = models.ForeignKey(
        'Event',
        related_name='cdms',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
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
        max_digits=100, decimal_places=100, null=True, blank=True
    )
    collision_probability_method = models.CharField(max_length=64, null=True, blank=True)

    # Additional comments or metadata
    comments = models.JSONField(null=True, blank=True)

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

    def calculate_covariance_rsse(self, covariance_matrix):
        """Calculate Root Sum Squared Error of a covariance matrix.
        
        RSSE = sqrt(sum of squared diagonal elements)
        This represents the combined uncertainty from all 6 dimensions.
        
        Args:
            covariance_matrix: 6x6 or 3x3 nested array (JSON)
            
        Returns:
            float: RSSE value, or None if matrix is invalid
        """
        if not covariance_matrix:
            return None
        
        try:
            # Sum the diagonal elements squared
            rsse_squared = 0
            for i in range(len(covariance_matrix)):
                if i < len(covariance_matrix[i]):
                    rsse_squared += covariance_matrix[i][i] ** 2
            
            # Return square root
            return rsse_squared ** 0.5
        except (TypeError, IndexError, ValueError):
            return None
    
    def get_obj1_covariance_rsse(self):
        """Get RSSE for Object 1 covariance matrix."""
        return self.calculate_covariance_rsse(self.obj1_covariance_matrix)
    
    def get_obj2_covariance_rsse(self):
        """Get RSSE for Object 2 covariance matrix."""
        return self.calculate_covariance_rsse(self.obj2_covariance_matrix)

    def __str__(self):
        return f"CDM {self.cdm_id} @ {self.tca}"
