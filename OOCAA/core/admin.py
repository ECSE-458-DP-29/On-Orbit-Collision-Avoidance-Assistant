from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# Import models from the models package and register them in the admin site.
from core.models import User, SpaceObject, CDM


@admin.register(SpaceObject)
class SpaceObjectAdmin(admin.ModelAdmin):
	list_display = ("object_designator", "object_name", "object_type", "operator_organization", "maneuverable")
	search_fields = ("object_designator", "object_name", "operator_organization")


@admin.register(CDM)
class CDMAdmin(admin.ModelAdmin):
	list_display = ("id", "tca", "obj1", "obj2", "collision_probability")
	list_filter = ("collision_probability_method",)
	search_fields = ("obj1__object_designator", "obj2__object_designator")


# Register custom user model with enhanced admin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff', 'is_superuser')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    # Add role field to the user edit form
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Role & Permissions', {'fields': ('role',)}),
    )
    
    # Add role field to the user creation form
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'role'),
        }),
    )
