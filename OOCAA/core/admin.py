from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, CDM, ManeuverPlan, CollisionAnalysis


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for custom User model"""
    list_display = ['username', 'email', 'organization', 'role', 'is_staff', 'created_at']
    list_filter = ['role', 'is_staff', 'is_active']
    search_fields = ['username', 'email', 'organization']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('organization', 'role')}),
    )


@admin.register(CDM)
class CDMAdmin(admin.ModelAdmin):
    """Admin interface for CDM model"""
    list_display = ['cdm_id', 'tca', 'object1_name', 'object2_name', 'collision_probability', 
                    'risk_level', 'status', 'created_at']
    list_filter = ['status', 'risk_level', 'originator', 'created_at']
    search_fields = ['cdm_id', 'object1_name', 'object2_name', 'message_id']
    date_hierarchy = 'tca'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Metadata', {
            'fields': ('cdm_id', 'creation_date', 'originator', 'message_for', 'message_id')
        }),
        ('Primary Object', {
            'fields': ('object1_name', 'object1_designator', 'object1_catalog_name', 'object1_object_type',
                      'object1_position', 'object1_velocity', 'object1_covariance_matrix')
        }),
        ('Secondary Object', {
            'fields': ('object2_name', 'object2_designator', 'object2_catalog_name', 'object2_object_type',
                      'object2_position', 'object2_velocity', 'object2_covariance_matrix')
        }),
        ('Conjunction Data', {
            'fields': ('tca', 'miss_distance', 'relative_speed', 'collision_probability', 
                      'collision_probability_method')
        }),
        ('Risk Assessment', {
            'fields': ('risk_level', 'status', 'notes')
        }),
        ('Tracking', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at')
        }),
    )


@admin.register(ManeuverPlan)
class ManeuverPlanAdmin(admin.ModelAdmin):
    """Admin interface for ManeuverPlan model"""
    list_display = ['maneuver_id', 'cdm', 'maneuver_type', 'maneuver_time', 'status', 'created_at']
    list_filter = ['status', 'maneuver_type', 'created_at']
    search_fields = ['maneuver_id', 'cdm__cdm_id']
    date_hierarchy = 'maneuver_time'
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CollisionAnalysis)
class CollisionAnalysisAdmin(admin.ModelAdmin):
    """Admin interface for CollisionAnalysis model"""
    list_display = ['analysis_id', 'analysis_method', 'combined_risk_score', 'recommended_action', 'performed_at']
    list_filter = ['recommended_action', 'performed_at']
    search_fields = ['analysis_id', 'recommendation']
    date_hierarchy = 'performed_at'
    readonly_fields = ['performed_at', 'updated_at']
    filter_horizontal = ['cdms']
