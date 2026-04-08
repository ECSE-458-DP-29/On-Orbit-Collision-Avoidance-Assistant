"""
Unit tests for core models.
"""
import pytest
from datetime import datetime, timezone
from core.models import SpaceObject, CDM, Event
from core.tests.factories import SpaceObjectFactory, CDMFactory, EventFactory


@pytest.mark.django_db
class TestSpaceObject:
    """Unit tests for SpaceObject model."""

    def test_create_space_object(self):
        """Test creating a space object."""
        obj = SpaceObject.objects.create(
            object_designator='TEST001',
            object_name='Test Satellite',
            object_type='PAYLOAD',
            operator_organization='Test Agency',
            maneuverable=True,
        )
        assert obj.id is not None
        assert obj.object_designator == 'TEST001'
        assert obj.maneuverable is True

    def test_space_object_unique_constraint(self):
        """Test that object_designator is unique."""
        SpaceObjectFactory(object_designator='UNIQUE001')
        with pytest.raises(Exception):  # IntegrityError
            SpaceObjectFactory(object_designator='UNIQUE001')

    def test_space_object_string_representation(self):
        """Test string representation of space object."""
        obj = SpaceObjectFactory(
            object_designator='SAT001',
            object_name='Test Sat'
        )
        assert str(obj) == 'SAT001 (Test Sat)'

    def test_space_object_defaults(self):
        """Test default values for space object."""
        obj = SpaceObjectFactory()
        assert obj.maneuverable is False  # Default value
        assert obj.object_designator is not None


@pytest.mark.django_db
class TestEvent:
    """Unit tests for Event model."""

    def test_create_event(self):
        """Test creating an event."""
        obj1 = SpaceObjectFactory()
        obj2 = SpaceObjectFactory()
        tca = datetime(2025, 1, 25, 7, 24, 13, tzinfo=timezone.utc)
        
        event = Event.objects.create(
            obj1=obj1,
            obj2=obj2,
            representative_tca=tca,
        )
        assert event.id is not None
        assert event.obj1 == obj1
        assert event.obj2 == obj2
        assert event.representative_tca == tca

    def test_event_unique_constraint(self):
        """Test unique constraint on event (obj1, obj2, tca)."""
        obj1 = SpaceObjectFactory()
        obj2 = SpaceObjectFactory()
        tca = datetime(2025, 1, 25, 7, 24, 13, tzinfo=timezone.utc)
        
        # Create first event
        Event.objects.create(obj1=obj1, obj2=obj2, representative_tca=tca)
        
        # Try to create duplicate - should fail
        with pytest.raises(Exception):  # IntegrityError
            Event.objects.create(obj1=obj1, obj2=obj2, representative_tca=tca)

    def test_event_string_representation(self):
        """Test string representation of event."""
        event = EventFactory()
        expected = (
            f"Event {event.id}: {event.obj1.object_designator} & "
            f"{event.obj2.object_designator} @ {event.representative_tca}"
        )
        assert str(event) == expected

    def test_event_cascade_delete(self):
        """Test that deleting a space object cascades to events."""
        obj1 = SpaceObjectFactory()
        obj2 = SpaceObjectFactory()
        event = Event.objects.create(
            obj1=obj1,
            obj2=obj2,
            representative_tca=datetime.now(timezone.utc),
        )
        
        event_id = event.id
        obj1.delete()
        
        # Event should be deleted
        assert not Event.objects.filter(id=event_id).exists()


@pytest.mark.django_db
class TestCDM:
    """Unit tests for CDM model."""

    def test_create_cdm(self, cdm_data):
        """Test creating a CDM."""
        assert cdm_data.id is not None
        assert cdm_data.message_id == '5741_conj50_7046'
        assert cdm_data.collision_probability == 0.000000013470

    def test_cdm_state_vectors(self, cdm_data):
        """Test CDM state vectors are stored correctly."""
        assert 'x_km' in cdm_data.state_vector_obj1
        assert 'x_dot_km_s' in cdm_data.state_vector_obj2
        assert float(cdm_data.state_vector_obj1['x_km']) == pytest.approx(893.288, rel=0.01)

    def test_cdm_relationships(self):
        """Test CDM foreign key relationships."""
        obj1 = SpaceObjectFactory()
        obj2 = SpaceObjectFactory()
        event = EventFactory(obj1=obj1, obj2=obj2)
        
        cdm = CDMFactory(obj1=obj1, obj2=obj2, event=event)
        
        assert cdm.obj1 == obj1
        assert cdm.obj2 == obj2
        assert cdm.event == event

    def test_cdm_nullable_fields(self):
        """Test CDM nullable fields."""
        obj1 = SpaceObjectFactory()
        obj2 = SpaceObjectFactory()
        tca = datetime.now(timezone.utc)
        
        cdm = CDM.objects.create(
            obj1=obj1,
            obj2=obj2,
            tca=tca,
        )
        
        assert cdm.message_id is None
        assert cdm.collision_probability is None
        assert cdm.event is None

    def test_cdm_factory(self):
        """Test CDMFactory generates valid CDM objects."""
        cdm = CDMFactory()
        assert cdm.id is not None
        assert cdm.obj1 is not None
        assert cdm.obj2 is not None
        assert cdm.tca > cdm.creation_date
        assert cdm.miss_distance_m > 0
        assert cdm.collision_probability > 0
