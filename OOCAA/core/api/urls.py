"""API urls for the core app.

Provides RESTful endpoints for CDM and SpaceObject management.
"""

from django.urls import path
from .views import (
    api_index,
    CDMListCreateView,
    CDMDetailView,
    SpaceObjectListCreateView,
    EventListView,
    CalculatePcView,
    BatchCalculatePcView,
    ParseCDMJsonView,
)

urlpatterns = [
    # Landing page
    path('', api_index, name='api-index'),
    
    # CDM endpoints
    path('cdms/', CDMListCreateView.as_view(), name='cdm-list-create'),
    path('cdms/<int:pk>/', CDMDetailView.as_view(), name='cdm-detail'),
    path('cdms/parse/', ParseCDMJsonView.as_view(), name='cdm-parse'),
    
    # Pc calculation endpoints
    path('cdms/<int:pk>/calculate-pc/', CalculatePcView.as_view(), name='cdm-calculate-pc'),
    path('cdms/batch-calculate-pc/', BatchCalculatePcView.as_view(), name='cdm-batch-calculate-pc'),
    
    # SpaceObject endpoints
    path('spaceobjects/', SpaceObjectListCreateView.as_view(), name='spaceobject-list-create'),
    # Event endpoints
    path('events/', EventListView.as_view(), name='event-list'),
]