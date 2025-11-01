from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    """
    Custom User model for authentication
    """
    organization = models.CharField(max_length=255, blank=True, null=True)
    role = models.CharField(max_length=50, choices=[
        ('admin', 'Administrator'),
        ('analyst', 'Analyst'),
        ('viewer', 'Viewer'),
    ], default='viewer')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username


class CDM(models.Model):
    """
    Conjunction Data Message model
    Stores information about potential satellite conjunctions
    """
    # Metadata
    cdm_id = models.CharField(max_length=100, unique=True, db_index=True)
    creation_date = models.DateTimeField()
    originator = models.CharField(max_length=255)
    message_for = models.CharField(max_length=255)
    message_id = models.CharField(max_length=100)
    
    # Primary Object (e.g., protected satellite)
    object1_name = models.CharField(max_length=255)
    object1_designator = models.CharField(max_length=50)
    object1_catalog_name = models.CharField(max_length=50, default='SATCAT')
    object1_object_type = models.CharField(max_length=50, blank=True, null=True)
    
    # Secondary Object (e.g., debris or other satellite)
    object2_name = models.CharField(max_length=255)
    object2_designator = models.CharField(max_length=50)
    object2_catalog_name = models.CharField(max_length=50, default='SATCAT')
    object2_object_type = models.CharField(max_length=50, blank=True, null=True)
    
    # Conjunction Information
    tca = models.DateTimeField(help_text="Time of Closest Approach")
    miss_distance = models.FloatField(help_text="Miss distance in meters")
    relative_speed = models.FloatField(help_text="Relative speed in m/s")
    
    # Probability of Collision
    collision_probability = models.FloatField(help_text="Probability of collision")
    collision_probability_method = models.CharField(max_length=100, blank=True, null=True)
    
    # Covariance and State Vectors (stored as JSON for flexibility)
    object1_position = models.JSONField(help_text="Position vector [x, y, z] in km")
    object1_velocity = models.JSONField(help_text="Velocity vector [vx, vy, vz] in km/s")
    object1_covariance_matrix = models.JSONField(blank=True, null=True)
    
    object2_position = models.JSONField(help_text="Position vector [x, y, z] in km")
    object2_velocity = models.JSONField(help_text="Velocity vector [vx, vy, vz] in km/s")
    object2_covariance_matrix = models.JSONField(blank=True, null=True)
    
    # Additional Risk Assessment
    risk_level = models.CharField(max_length=20, choices=[
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ], default='low')
    
    # Screening and Analysis Status
    status = models.CharField(max_length=50, choices=[
        ('received', 'Received'),
        ('analyzing', 'Analyzing'),
        ('analyzed', 'Analyzed'),
        ('maneuver_planned', 'Maneuver Planned'),
        ('maneuver_executed', 'Maneuver Executed'),
        ('passed', 'Passed'),
        ('false_alarm', 'False Alarm'),
    ], default='received')
    
    # User and Timestamps
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='cdms_created')
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='cdms_updated')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Notes and Comments
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-tca']
        verbose_name = "CDM"
        verbose_name_plural = "CDMs"
    
    def __str__(self):
        return f"CDM {self.cdm_id} - TCA: {self.tca}"


class ManeuverPlan(models.Model):
    """
    Collision Avoidance Maneuver Plan
    """
    cdm = models.ForeignKey(CDM, on_delete=models.CASCADE, related_name='maneuver_plans')
    maneuver_id = models.CharField(max_length=100, unique=True)
    
    # Maneuver Details
    maneuver_type = models.CharField(max_length=50, choices=[
        ('in_track', 'In-Track'),
        ('cross_track', 'Cross-Track'),
        ('radial', 'Radial'),
        ('combined', 'Combined'),
    ])
    
    delta_v = models.JSONField(help_text="Delta-V vector [x, y, z] in m/s")
    maneuver_time = models.DateTimeField()
    execution_duration = models.FloatField(help_text="Duration in seconds")
    
    # Post-Maneuver Predictions
    new_miss_distance = models.FloatField(help_text="Predicted miss distance after maneuver in meters")
    new_collision_probability = models.FloatField(help_text="Predicted collision probability after maneuver")
    
    # Fuel and Resource Cost
    fuel_cost = models.FloatField(help_text="Fuel cost in kg or percent", blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=50, choices=[
        ('proposed', 'Proposed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('scheduled', 'Scheduled'),
        ('executed', 'Executed'),
        ('cancelled', 'Cancelled'),
    ], default='proposed')
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Maneuver {self.maneuver_id} for CDM {self.cdm.cdm_id}"


class CollisionAnalysis(models.Model):
    """
    Detailed collision analysis between multiple CDMs
    """
    analysis_id = models.CharField(max_length=100, unique=True)
    cdms = models.ManyToManyField(CDM, related_name='analyses')
    
    # Analysis Parameters
    analysis_method = models.CharField(max_length=100)
    time_window_start = models.DateTimeField()
    time_window_end = models.DateTimeField()
    
    # Results
    combined_risk_score = models.FloatField()
    recommendation = models.TextField()
    recommended_action = models.CharField(max_length=50, choices=[
        ('monitor', 'Continue Monitoring'),
        ('maneuver', 'Execute Maneuver'),
        ('no_action', 'No Action Required'),
    ])
    
    # Metadata
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    performed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-performed_at']
        verbose_name = "Collision Analysis"
        verbose_name_plural = "Collision Analyses"
    
    def __str__(self):
        return f"Analysis {self.analysis_id} - {self.performed_at}"
