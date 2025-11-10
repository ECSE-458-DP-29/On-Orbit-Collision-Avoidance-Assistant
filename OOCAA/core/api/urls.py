"""API urls for the core app.

This file currently provides a simple landing view at the package root
(`/api/`). Add DRF routers or additional URL patterns here when you
enable DRF and implement viewsets.
"""

from django.urls import path
from .views import api_index
from .views import CDMCreateView, SpaceObjectListCreateView

urlpatterns = [
    path('', api_index, name='api-index'), #THIS IS AN EXAPLE VIEW
    path('cdms/', CDMCreateView.as_view(), name='cdm-create'),
    path('spaceobjects/', SpaceObjectListCreateView.as_view(), name='spaceobject-list'),
    # future endpoints: path('spaceobjects/', include(...)) or DRF router
]
