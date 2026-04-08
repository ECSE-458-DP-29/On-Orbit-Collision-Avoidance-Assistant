"""
pytest configuration and shared fixtures for testing.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from core.models import SpaceObject, CDM
from datetime import datetime, timezone

User = get_user_model()


@pytest.fixture
def api_client():
    """Provide a DRF API client for integration tests."""
    return APIClient()


@pytest.fixture
def authenticated_client(api_client):
    """Provide an authenticated API client."""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def test_user():
    """Create a test user."""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def space_object_1():
    """Create a test space object (satellite 1)."""
    return SpaceObject.objects.create(
        object_designator='39265',
        object_name='CASSIOPE',
        object_type='PAYLOAD',
        operator_organization='CSA',
        maneuverable=False,
    )


@pytest.fixture
def space_object_2():
    """Create a test space object (satellite 2)."""
    return SpaceObject.objects.create(
        object_designator='44322',
        object_name='RCM-1',
        object_type='PAYLOAD',
        operator_organization='CSA',
        maneuverable=True,
    )


@pytest.fixture
def cdm_data(space_object_1, space_object_2):
    """Create a test CDM object."""
    return CDM.objects.create(
        cdm_id='CDM_001',
        message_id='5741_conj50_7046',
        creation_date=datetime(2025, 1, 20, 8, 12, 49, tzinfo=timezone.utc),
        ccsds_version='1.0',
        originator='CSpoc',
        obj1=space_object_1,
        obj2=space_object_2,
        tca=datetime(2025, 1, 25, 7, 24, 13, tzinfo=timezone.utc),
        miss_distance_m=31612.0,
        relative_speed_ms=13.5,
        collision_probability=0.000000013470,
        state_vector_obj1={
            'x_km': '893.2881302848575',
            'y_km': '742.1116994805794',
            'z_km': '7170.904591941126',
            'x_dot_km_s': '-4.1894033396829595',
            'y_dot_km_s': '5.920251359621457',
            'z_dot_km_s': '0.02921623106465332',
        },
        state_vector_obj2={
            'x_km': '1786.393860569715',
            'y_km': '1502.7850989611588',
            'z_km': '14316.21998388225',
            'x_dot_km_s': '-8.403406679365919',
            'y_dot_km_s': '21.629002719242916',
            'z_dot_km_s': '7.160232462129307',
        },
    )


@pytest.fixture
def db_rollback(db):
    """Ensure database changes are rolled back after each test (implicit in pytest-django)."""
    return db
