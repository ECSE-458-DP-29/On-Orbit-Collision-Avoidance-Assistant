"""API urls for the core app.

Provides RESTful endpoints for CDM and SpaceObject management.
"""

from django.urls import path
from .views import (
    api_index,
    CDMListCreateView,
    CDMDetailView,
    SpaceObjectListCreateView,
    EventListView
)

urlpatterns = [
    # Landing page
    path('', api_index, name='api-index'),
    
    # CDM endpoints
    path('cdms/', CDMListCreateView.as_view(), name='cdm-list-create'),
    path('cdms/<int:pk>/', CDMDetailView.as_view(), name='cdm-detail'),
    
    # SpaceObject endpoints
    path('spaceobjects/', SpaceObjectListCreateView.as_view(), name='spaceobject-list-create'),
    # Event endpoints
    path('events/', EventListView.as_view(), name='event-list'),
]