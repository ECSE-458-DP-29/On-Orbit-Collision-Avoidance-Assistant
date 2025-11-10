"""Simple, non-DRF views for the `core.api` package.

This file provides a tiny render-based view so visiting `/api/` can
show an informational HTML page before you wire full API endpoints.
"""
from django.shortcuts import render
from django.shortcuts import render

from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CDMSerializer, SpaceObjectSerializer
from core.services import create_cdm
from core.models.spaceobject import SpaceObject


def api_index(request):
    """Render a small landing page for the API area."""
    return render(request, "api_index.html", {"message": "Core API landing page"})


class CDMCreateView(APIView):
    """Controller for creating CDMs using the service layer.

    The view keeps validation in the serializer and delegates persistence
    and business rules to `core.services.create_cdm`.
    """

    def post(self, request, *args, **kwargs):
        serializer = CDMSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Delegate creation to service layer which returns the created model
        try:
            cdm = create_cdm(serializer.validated_data)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        # Re-serialize the saved model for the response
        out = CDMSerializer(cdm)
        return Response(out.data, status=status.HTTP_201_CREATED)


class SpaceObjectListCreateView(generics.ListCreateAPIView):
    """List and create SpaceObject instances via API."""
    queryset = SpaceObject.objects.all()
    serializer_class = SpaceObjectSerializer


__all__ = ["api_index", "CDMCreateView", "SpaceObjectListCreateView"]
