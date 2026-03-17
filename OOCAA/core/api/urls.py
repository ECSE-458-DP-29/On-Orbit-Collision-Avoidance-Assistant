"""API urls for the core app.

Provides RESTful endpoints for CDM and SpaceObject management.
"""

from django.urls import path
from .views import (
    api_index,
    manage_cdms,
    upload_cdm,
    globe,
    view_cdm,
    dashboard,
    CDMListCreateView,
    CDMDetailView,
    SpaceObjectListCreateView,
    EventListView,
    CalculatePcView,
    BatchCalculatePcView,
    ParseCDMJsonView,
    DashboardDataView,
)

urlpatterns = [
    # Landing page
    path('api/', api_index, name='api-index'),
    path('globe/', globe, name='globe'),
    path('dashboard/', dashboard, name='dashboard'),
    
    # Management pages
    path('manage/cdms/', manage_cdms, name='manage-cdms'),
    path('upload/cdm/', upload_cdm, name='upload-cdm'),
    
    # CDM endpoints
    path('cdms/', CDMListCreateView.as_view(), name='cdm-list-create'),
    path('cdms/<int:pk>/', view_cdm, name='cdm-detail'),
    path('cdms/parse/', ParseCDMJsonView.as_view(), name='cdm-parse'),
    
    # Pc calculation endpoints
    path('cdms/<int:pk>/calculate-pc/', CalculatePcView.as_view(), name='cdm-calculate-pc'),
    path('cdms/batch-calculate-pc/', BatchCalculatePcView.as_view(), name='cdm-batch-calculate-pc'),
    
    # SpaceObject endpoints
    path('spaceobjects/', SpaceObjectListCreateView.as_view(), name='spaceobject-list-create'),
    # Event endpoints
    path('events/', EventListView.as_view(), name='event-list'),
    
    # Dashboard API endpoints
    path('api/dashboard-data/', DashboardDataView.as_view(), name='dashboard-data'),
]