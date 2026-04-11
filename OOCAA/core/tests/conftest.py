import pytest
from datetime import datetime, timezone
from core.tests.factories import CDMFactory, UserFactory


@pytest.fixture
def cdm_data():
    """Fixture for creating a CDM with test data."""
    return CDMFactory(
        message_id='5741_conj50_7046',
        collision_probability=0.000000013470
    )


@pytest.fixture
def authenticated_user():
    """Fixture for creating an authenticated user."""
    return UserFactory(username='testuser', email='test@example.com')


@pytest.fixture
def cdm_json_data():
    """Fixture for CDM JSON test data."""
    return {
        "CCSDS_CDM_VERS": "1.0",
        "CREATION_DATE": "2025-01-20T08:12:49Z",
        "ORIGINATOR": "CSpoc",
        "MESSAGE_ID": "TEST_MSG_001",
        "TCA": "2025-01-25T07:24:13Z",
        "MISS_DISTANCE": "31612",
        "COLLISION_PROBABILITY": "1.3e-08",
        "SAT1_OBJECT_DESIGNATOR": "39265",
        "SAT1_OBJECT_NAME": "TESTSAT1",
        "SAT1_OBJECT_TYPE": "PAYLOAD",
        "SAT1_OPERATOR_ORGANIZATION": "CSA",
        "SAT1_MANEUVERABLE": "NO",
        "SAT1_X": "893.29",
        "SAT1_Y": "742.11",
        "SAT1_Z": "7170.90",
        "SAT1_X_DOT": "-4.19",
        "SAT1_Y_DOT": "5.92",
        "SAT1_Z_DOT": "0.03",
        "SAT2_OBJECT_DESIGNATOR": "44322",
        "SAT2_OBJECT_NAME": "TESTSAT2",
        "SAT2_OBJECT_TYPE": "PAYLOAD",
        "SAT2_OPERATOR_ORGANIZATION": "CSA",
        "SAT2_MANEUVERABLE": "YES",
        "SAT2_X": "1786.39",
        "SAT2_Y": "1502.79",
        "SAT2_Z": "14316.22",
        "SAT2_X_DOT": "-8.40",
        "SAT2_Y_DOT": "21.63",
        "SAT2_Z_DOT": "7.16",
    }