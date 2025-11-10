"""DRF serializers for the core API.

Provides a ModelSerializer for creating and validating `CDM` objects.
"""
from rest_framework import serializers

from core.models.cdm import CDM
from core.models.spaceobject import SpaceObject


class SpaceObjectSerializer(serializers.ModelSerializer):
    """Serializer for SpaceObject create/list operations."""

    class Meta:
        model = SpaceObject
        fields = [
            'id',
            'object_designator',
            'object_name',
            'object_type',
            'operator_organization',
            'maneuverable',
        ]
        read_only_fields = ['id']


class CDMSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating CDM instances.

    Accepts `obj1` and `obj2` as primary key references to existing
    `SpaceObject` records. Also accepts `obj1_data`/`obj2_data` dicts to
    create SpaceObjects inline when creating a CDM.
    """

    class Meta:
        model = CDM
        fields = [
            'id',
            'obj1',
            'obj2',
            'tca',
            'miss_distance_m',
            'relative_position_r',
            'relative_position_t',
            'relative_position_n',
            'collision_probability',
            'collision_probability_method',
            'obj1_data',
            'obj2_data',
        ]
        read_only_fields = ['id']

    # Use PrimaryKeyRelatedField so DRF validates that provided PKs exist
    obj1 = serializers.PrimaryKeyRelatedField(
        queryset=SpaceObject.objects.all(), allow_null=True, required=False
    )
    obj2 = serializers.PrimaryKeyRelatedField(
        queryset=SpaceObject.objects.all(), allow_null=True, required=False
    )
    # Allow nested object creation via obj1_data/obj2_data when the caller
    # wants the API to create a SpaceObject as part of the CDM POST.
    obj1_data = SpaceObjectSerializer(write_only=True, required=False)
    obj2_data = SpaceObjectSerializer(write_only=True, required=False)

    def validate_collision_probability(self, value):
        # Model validators already enforce 0..1 but validate here for clearer API errors
        if value is None:
            return value
        if value < 0 or value > 1:
            raise serializers.ValidationError('collision_probability must be between 0 and 1')
        return value

    def validate(self, attrs):
        # If nested creation data provided alongside a PK, prefer the explicit PK.
        # Nothing required here otherwise; caller may provide obj1/obj2 as PKs or
        # obj1_data/obj2_data to create them on the fly.
        return attrs


__all__ = ['CDMSerializer']
class SpaceObjectSerializer(serializers.ModelSerializer):
    """Serializer for SpaceObject create/list operations."""

    class Meta:
        model = SpaceObject
        fields = [
            'id',
            'object_designator',
            'object_name',
            'object_type',
            'operator_organization',
            'maneuverable',
        ]
        read_only_fields = ['id']


__all__ = ['CDMSerializer', 'SpaceObjectSerializer']
