import unittest
from django.test import TestCase
from rest_framework.test import APITestCase
from core.tests.factories import UserFactory, SpaceObjectFactory, CDMFactory, EventFactory

try:
    from core.api.serializers import CDMSerializer, SpaceObjectSerializer, EventSerializer
    SERIALIZERS_AVAILABLE = True
except ImportError:
    SERIALIZERS_AVAILABLE = False


@unittest.skipUnless(SERIALIZERS_AVAILABLE, "Serializers not yet implemented")
class SpaceObjectSerializerTestCase(TestCase):
    """Tests for SpaceObjectSerializer."""

    def test_space_object_serializer_valid(self):
        """Test serializing valid space object."""
        obj = SpaceObjectFactory()
        serializer = SpaceObjectSerializer(obj)
        self.assertEqual(serializer.data['object_designator'], obj.object_designator)
        self.assertEqual(serializer.data['object_name'], obj.object_name)

    def test_space_object_serializer_create(self):
        """Test creating space object via serializer."""
        data = {
            'object_designator': '25544',
            'object_name': 'ISS',
            'object_type': 'PAYLOAD',
            'operator_organization': 'NASA'
        }
        serializer = SpaceObjectSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        obj = serializer.save()
        self.assertEqual(obj.object_designator, '25544')


@unittest.skipUnless(SERIALIZERS_AVAILABLE, "Serializers not yet implemented")
class CDMSerializerTestCase(TestCase):
    """Tests for CDMSerializer."""

    def test_cdm_serializer_valid(self):
        """Test serializing valid CDM."""
        cdm = CDMFactory()
        serializer = CDMSerializer(cdm)
        # Check that essential fields are present
        self.assertIn('id', serializer.data)
        self.assertIn('collision_probability', serializer.data)

    def test_cdm_serializer_includes_nested_objects(self):
        """Test CDM serializer includes nested space objects."""
        cdm = CDMFactory()
        serializer = CDMSerializer(cdm)
        self.assertIn('obj1', serializer.data)
        self.assertIn('obj2', serializer.data)


@unittest.skipUnless(SERIALIZERS_AVAILABLE, "Serializers not yet implemented")
class EventSerializerTestCase(TestCase):
    """Tests for EventSerializer."""

    def test_event_serializer_valid(self):
        """Test serializing valid event."""
        event = EventFactory()
        serializer = EventSerializer(event)
        self.assertIn('obj1', serializer.data)
        self.assertIn('obj2', serializer.data)
        self.assertIn('representative_tca', serializer.data)