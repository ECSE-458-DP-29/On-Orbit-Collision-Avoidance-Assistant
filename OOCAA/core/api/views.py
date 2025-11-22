"""API views for CDM and SpaceObject management."""
from django.shortcuts import render

from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CDMSerializer, SpaceObjectSerializer, EventSerializer
from core.services import (
    create_cdm,
    get_cdm,
    list_cdms,
    update_cdm,
    delete_cdm,
    list_events,

)
from core.models.spaceobject import SpaceObject
from core.services.cdm_service import parse_cdm_json


def api_index(request):
    """Render a small landing page for the API area."""
    return render(request, "api_index.html", {"message": "Core API landing page"})


class CDMListCreateView(APIView):
    """List all CDMs or create a new CDM.
    
    GET: List all CDMs with optional filtering
    POST: Create a new CDM
    """
    
    def get(self, request, *args, **kwargs):
        """List all CDMs with optional filtering."""
        # Extract filter parameters from query string
        filters = {}
        
        if 'obj1_id' in request.query_params:
            filters['obj1_id'] = request.query_params['obj1_id']
        
        if 'obj2_id' in request.query_params:
            filters['obj2_id'] = request.query_params['obj2_id']
        
        if 'event_id' in request.query_params:
            filters['event_id'] = request.query_params['event_id']
        
        if 'tca_after' in request.query_params:
            filters['tca_after'] = request.query_params['tca_after']
        
        if 'tca_before' in request.query_params:
            filters['tca_before'] = request.query_params['tca_before']
        
        if 'min_collision_probability' in request.query_params:
            filters['min_collision_probability'] = request.query_params['min_collision_probability']
        
        cdms = list_cdms(filters if filters else None)
        serializer = CDMSerializer(cdms, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request, *args, **kwargs):
        """Create a new CDM."""
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


class CDMDetailView(APIView):
    """Retrieve, update, or delete a specific CDM.
    
    GET: Retrieve a CDM by ID
    PUT: Update a CDM
    DELETE: Delete a CDM
    """
    
    def get(self, request, pk, *args, **kwargs):
        """Retrieve a specific CDM by ID."""
        cdm = get_cdm(pk)
        if not cdm:
            return Response(
                {"detail": "CDM not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CDMSerializer(cdm)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk, *args, **kwargs):
        """Update a CDM."""
        return self._update(request, pk, partial=True)
    
    
    def _update(self, request, pk, partial=False):
        """Helper method to handle both PUT and PATCH."""
        cdm = get_cdm(pk)
        if not cdm:
            return Response(
                {"detail": "CDM not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = CDMSerializer(cdm, data=request.data, partial=partial)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            updated_cdm = update_cdm(pk, serializer.validated_data)
            if not updated_cdm:
                return Response(
                    {"detail": "CDM not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        
        out = CDMSerializer(updated_cdm)
        return Response(out.data, status=status.HTTP_200_OK)
    
    def delete(self, request, pk, *args, **kwargs):
        """Delete a specific CDM."""
        deleted = delete_cdm(pk)
        if not deleted:
            return Response(
                {"detail": "CDM not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class SpaceObjectListCreateView(generics.ListCreateAPIView):
    """List and create SpaceObject instances via API."""
    queryset = SpaceObject.objects.all()
    serializer_class = SpaceObjectSerializer

class EventListView(APIView):
    """List all events with optional filtering.
    
    GET: List all events with their associated CDMs and SpaceObject details
    """
    
    def get(self, request, *args, **kwargs):
        """List all events with optional filtering.
        
        Query Parameters:
        - object_id: Filter by object ID (matches if object is either obj1 or obj2)
        - tca_after: Filter events with TCA after this datetime (ISO 8601)
        - tca_before: Filter events with TCA before this datetime (ISO 8601)
        - min_cdm_count: Filter events with at least this many CDMs (integer)
        """
        # Extract filter parameters from query string
        filters = {}
        
        if 'object_id' in request.query_params:
            filters['object_id'] = request.query_params['object_id']
        
        if 'tca_after' in request.query_params:
            filters['tca_after'] = request.query_params['tca_after']
        
        if 'tca_before' in request.query_params:
            filters['tca_before'] = request.query_params['tca_before']
        
        if 'min_cdm_count' in request.query_params:
            try:
                filters['min_cdm_count'] = int(request.query_params['min_cdm_count'])
            except ValueError:
                return Response(
                    {"detail": "min_cdm_count must be an integer."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        events = list_events(filters if filters else None)
        serializer = EventSerializer(events, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ParseCDMJsonView(APIView):
    """API endpoint to parse a CDM JSON and create a CDM object."""

    def post(self, request, *args, **kwargs):
        try:
            # Extract JSON data from the request body
            ## TODO: VERIFY FORMAT OF THE DATA LIST OR DICT
            data = request.data
            # Call the parse_cdm_json function
            cdm, obj1, obj2 = parse_cdm_json(data)
            # Return the created CDM's ID as a response
            return Response({"cdm_id": cdm.id, "space_obj1_id": obj1.id,"space_obj2_id": obj2.id,}, status=status.HTTP_201_CREATED)
        except Exception as e:
            # Handle errors and return a 400 Bad Request response
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
__all__ = [
    "api_index",
    "CDMListCreateView",
    "CDMDetailView",
    "SpaceObjectListCreateView",
    "EventListView",
    "ParseCDMJsonView",
]