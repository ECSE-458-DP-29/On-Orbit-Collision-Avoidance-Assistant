from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import CDM, ManeuverPlan, CollisionAnalysis

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration
    """
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'password_confirm', 'first_name', 'last_name', 'organization', 'role']
        read_only_fields = ['id']

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data.get('email', ''),
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            organization=validated_data.get('organization', ''),
            role=validated_data.get('role', 'viewer')
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user details
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'organization', 'role', 'created_at']
        read_only_fields = ['id', 'created_at']


class CDMSerializer(serializers.ModelSerializer):
    """
    Serializer for CDM (Conjunction Data Message)
    """
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_username = serializers.CharField(source='updated_by.username', read_only=True)

    class Meta:
        model = CDM
        fields = '__all__'
        read_only_fields = ['created_by', 'updated_by', 'created_at', 'updated_at']

    def validate_cdm_id(self, value):
        """Ensure CDM ID is unique"""
        if self.instance is None and CDM.objects.filter(cdm_id=value).exists():
            raise serializers.ValidationError("A CDM with this ID already exists.")
        return value

    def validate_collision_probability(self, value):
        """Ensure collision probability is between 0 and 1"""
        if not (0 <= value <= 1):
            raise serializers.ValidationError("Collision probability must be between 0 and 1.")
        return value

    def validate(self, attrs):
        """Validate position and velocity vectors"""
        # Validate object1 position and velocity
        if 'object1_position' in attrs:
            if not isinstance(attrs['object1_position'], list) or len(attrs['object1_position']) != 3:
                raise serializers.ValidationError({"object1_position": "Position must be a list of 3 values [x, y, z]."})
        
        if 'object1_velocity' in attrs:
            if not isinstance(attrs['object1_velocity'], list) or len(attrs['object1_velocity']) != 3:
                raise serializers.ValidationError({"object1_velocity": "Velocity must be a list of 3 values [vx, vy, vz]."})
        
        # Validate object2 position and velocity
        if 'object2_position' in attrs:
            if not isinstance(attrs['object2_position'], list) or len(attrs['object2_position']) != 3:
                raise serializers.ValidationError({"object2_position": "Position must be a list of 3 values [x, y, z]."})
        
        if 'object2_velocity' in attrs:
            if not isinstance(attrs['object2_velocity'], list) or len(attrs['object2_velocity']) != 3:
                raise serializers.ValidationError({"object2_velocity": "Velocity must be a list of 3 values [vx, vy, vz]."})
        
        return attrs


class CDMListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for listing CDMs
    """
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = CDM
        fields = ['id', 'cdm_id', 'tca', 'object1_name', 'object2_name', 'miss_distance', 
                  'collision_probability', 'risk_level', 'status', 'created_by_username', 'created_at']


class ManeuverPlanSerializer(serializers.ModelSerializer):
    """
    Serializer for Maneuver Plan
    """
    cdm_id = serializers.CharField(source='cdm.cdm_id', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = ManeuverPlan
        fields = '__all__'
        read_only_fields = ['created_by', 'created_at', 'updated_at']

    def validate_delta_v(self, value):
        """Validate delta-V vector"""
        if not isinstance(value, list) or len(value) != 3:
            raise serializers.ValidationError("Delta-V must be a list of 3 values [x, y, z].")
        return value

    def validate_new_collision_probability(self, value):
        """Ensure new collision probability is between 0 and 1"""
        if not (0 <= value <= 1):
            raise serializers.ValidationError("New collision probability must be between 0 and 1.")
        return value


class CollisionAnalysisSerializer(serializers.ModelSerializer):
    """
    Serializer for Collision Analysis
    """
    cdm_ids = serializers.SerializerMethodField()
    performed_by_username = serializers.CharField(source='performed_by.username', read_only=True)

    class Meta:
        model = CollisionAnalysis
        fields = '__all__'
        read_only_fields = ['performed_by', 'performed_at', 'updated_at']

    def get_cdm_ids(self, obj):
        return [cdm.cdm_id for cdm in obj.cdms.all()]

    def validate(self, attrs):
        """Ensure time window is valid"""
        if 'time_window_start' in attrs and 'time_window_end' in attrs:
            if attrs['time_window_start'] >= attrs['time_window_end']:
                raise serializers.ValidationError({"time_window_end": "End time must be after start time."})
        return attrs


class CollisionAnalysisDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for Collision Analysis with full CDM data
    """
    cdms = CDMListSerializer(many=True, read_only=True)
    performed_by_username = serializers.CharField(source='performed_by.username', read_only=True)

    class Meta:
        model = CollisionAnalysis
        fields = '__all__'
        read_only_fields = ['performed_by', 'performed_at', 'updated_at']
