import unittest
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from core.tests.factories import UserFactory, CDMFactory, SpaceObjectFactory, EventFactory

try:
    from core.api.views import CDMViewSet, SpaceObjectViewSet, EventViewSet
    VIEWS_AVAILABLE = True
except ImportError:
    VIEWS_AVAILABLE = False


@unittest.skipUnless(VIEWS_AVAILABLE, "Views not yet implemented")
class CDMViewSetTestCase(APITestCase):
    """Tests for CDM API ViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_list_cdms(self):
        """Test listing CDMs."""
        CDMFactory.create_batch(3)
        response = self.client.get(reverse('api:cdm-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_cdm(self):
        """Test retrieving a single CDM."""
        cdm = CDMFactory()
        response = self.client.get(reverse('api:cdm-detail', args=[cdm.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


@unittest.skipUnless(VIEWS_AVAILABLE, "Views not yet implemented")
class SpaceObjectViewSetTestCase(APITestCase):
    """Tests for SpaceObject API ViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_list_space_objects(self):
        """Test listing space objects."""
        SpaceObjectFactory.create_batch(5)
        response = self.client.get(reverse('api:spaceobject-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_space_object(self):
        """Test retrieving a single space object."""
        obj = SpaceObjectFactory()
        response = self.client.get(reverse('api:spaceobject-detail', args=[obj.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)


@unittest.skipUnless(VIEWS_AVAILABLE, "Views not yet implemented")
class EventViewSetTestCase(APITestCase):
    """Tests for Event API ViewSet."""

    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)

    def test_list_events(self):
        """Test listing events."""
        EventFactory.create_batch(3)
        response = self.client.get(reverse('api:event-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)