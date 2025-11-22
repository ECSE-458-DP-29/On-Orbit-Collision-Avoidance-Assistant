"""DRF serializers for the core API.

Provides a ModelSerializer for creating and validating `CDM` objects.
"""
from rest_framework import serializers

from core.models.cdm import CDM
from core.models.spaceobject import SpaceObject
from core.models.event import Event


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


class SpaceObjectNestedSerializer(serializers.ModelSerializer):
    """Serializer for nested SpaceObject creation within CDM.
    
    Skips uniqueness validation on object_designator since the service
    layer handles get_or_create logic.
    """

    class Meta:
        model = SpaceObject
        fields = [
            'object_designator',
            'object_name',
            'object_type',
            'operator_organization',
            'maneuverable',
        ]
        extra_kwargs = {
            # Remove the unique validator - service layer handles duplicates
            'object_designator': {'validators': []},
        }


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
            'event',
            'miss_distance_m',
            'relative_position_r',
            'relative_position_t',
            'relative_position_n',
            'collision_probability',
            'collision_probability_method',
            'obj1_data',
            'obj2_data',
            # State vectors (ECI frame)
            'obj1_position_x',
            'obj1_position_y',
            'obj1_position_z',
            'obj1_velocity_x',
            'obj1_velocity_y',
            'obj1_velocity_z',
            'obj2_position_x',
            'obj2_position_y',
            'obj2_position_z',
            'obj2_velocity_x',
            'obj2_velocity_y',
            'obj2_velocity_z',
            # Covariance matrices
            'obj1_covariance_matrix',
            'obj2_covariance_matrix',
            # Hard body radius
            'hard_body_radius',
        ]
        read_only_fields = ['id', 'event']

    # Use PrimaryKeyRelatedField so DRF validates that provided PKs exist
    obj1 = serializers.PrimaryKeyRelatedField(
        queryset=SpaceObject.objects.all(), allow_null=True, required=False
    )
    obj2 = serializers.PrimaryKeyRelatedField(
        queryset=SpaceObject.objects.all(), allow_null=True, required=False
    )
    # Use the nested serializer that skips uniqueness validation
    obj1_data = SpaceObjectNestedSerializer(write_only=True, required=False)
    obj2_data = SpaceObjectNestedSerializer(write_only=True, required=False)

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
        
        # Validate covariance matrices if provided
        for obj_num in [1, 2]:
            cov_key = f'obj{obj_num}_covariance_matrix'
            if cov_key in attrs and attrs[cov_key] is not None:
                cov_matrix = attrs[cov_key]
                
                if not isinstance(cov_matrix, list):
                    raise serializers.ValidationError({
                        cov_key: 'Covariance matrix must be a nested array (list of lists)'
                    })
                
                # Check dimensions (must be 3x3 or 6x6)
                n_rows = len(cov_matrix)
                if n_rows not in [3, 6]:
                    raise serializers.ValidationError({
                        cov_key: f'Covariance matrix must be 3x3 or 6x6, got {n_rows} rows'
                    })
                
                # Validate each row
                for i, row in enumerate(cov_matrix):
                    if not isinstance(row, list):
                        raise serializers.ValidationError({
                            cov_key: f'Row {i} is not a list'
                        })
                    if len(row) != n_rows:
                        raise serializers.ValidationError({
                            cov_key: f'Row {i} has {len(row)} elements, expected {n_rows}'
                        })
                    # Validate that all elements are numeric
                    for j, val in enumerate(row):
                        if not isinstance(val, (int, float)):
                            raise serializers.ValidationError({
                                cov_key: f'Element [{i}][{j}] is not numeric'
                            })
        
        # Validate hard body radius if provided
        if 'hard_body_radius' in attrs and attrs['hard_body_radius'] is not None:
            if attrs['hard_body_radius'] <= 0:
                raise serializers.ValidationError({
                    'hard_body_radius': 'Hard body radius must be greater than 0'
                })
        
        return attrs

class CDMMinimalSerializer(serializers.ModelSerializer):
    """Minimal CDM serializer for nested representation in Event."""
    
    class Meta:
        model = CDM
        fields = [
            'id',
            'tca',
            'miss_distance_m',
            'collision_probability',
            'collision_probability_method',
        ]


class EventSerializer(serializers.ModelSerializer):
    """Serializer for Event instances with nested CDMs and SpaceObjects."""
    
    # Nested representations for better readability
    obj1_details = SpaceObjectSerializer(source='obj1', read_only=True)
    obj2_details = SpaceObjectSerializer(source='obj2', read_only=True)
    cdms = CDMMinimalSerializer(many=True, read_only=True)
    cdm_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id',
            'obj1',
            'obj2',
            'obj1_details',
            'obj2_details',
            'representative_tca',
            'cdm_count',
            'cdms',
        ]
        read_only_fields = ['id']
    
    def get_cdm_count(self, obj):
        """Return the number of CDMs associated with this event."""
        return obj.cdms.count()


__all__ = [
    'CDMSerializer',
    'SpaceObjectSerializer',
    'EventSerializer',
    'CDMMinimalSerializer',
]