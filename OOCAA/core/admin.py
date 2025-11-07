from django.contrib import admin

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


# Register custom user model
admin.site.register(User)
