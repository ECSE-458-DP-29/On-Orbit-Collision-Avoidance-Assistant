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
from core.services.pc_calculation_service import (
    calculate_pc_multistep,
    calculate_pc_circle,
    calculate_pc_dilution,
    batch_calculate_pc,
    update_cdm_with_pc_result,
    PcCalculationError,
    MatlabEngineError,
)
from core.models.spaceobject import SpaceObject
from core.models.cdm import CDM


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


class CalculatePcView(APIView):
    """Calculate probability of collision for a specific CDM.
    
    POST: Trigger Pc calculation for a CDM using CARA MATLAB tools
    
    Request Body (optional):
    {
        "method": "multistep" | "circle" | "dilution",  // default: "multistep"
        "update_cdm": true | false,  // default: true
        "params": {}  // optional MATLAB parameters
    }
    
    Response:
    {
        "cdm_id": 123,
        "Pc": 1.23e-5,
        "method": "PcMultiStep",
        "details": {...},
        "success": true,
        "updated": true
    }
    """
    
    def post(self, request, pk, *args, **kwargs):
        """Calculate Pc for the specified CDM."""
        # Get the CDM
        try:
            cdm = CDM.objects.get(pk=pk)
        except CDM.DoesNotExist:
            return Response(
                {"detail": "CDM not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Extract parameters from request
        method = request.data.get('method', 'multistep').lower()
        update_cdm_flag = request.data.get('update_cdm', True)
        matlab_params = request.data.get('params', None)
        
        # Validate method
        if method not in ['multistep', 'circle', 'dilution']:
            return Response(
                {"detail": f"Invalid method: {method}. Must be 'multistep', 'circle', or 'dilution'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate Pc
        try:
            if method == 'multistep':
                result = calculate_pc_multistep(cdm, matlab_params)
            elif method == 'circle':
                result = calculate_pc_circle(cdm)
            elif method == 'dilution':
                result = calculate_pc_dilution(cdm, matlab_params)
            
            # Update CDM if requested
            if update_cdm_flag and result.get('success'):
                update_cdm_with_pc_result(cdm, result, save=True)
                result['updated'] = True
            else:
                result['updated'] = False
            
            result['cdm_id'] = cdm.id
            
            return Response(result, status=status.HTTP_200_OK)
            
        except PcCalculationError as e:
            return Response(
                {
                    "detail": str(e),
                    "error_type": "PcCalculationError",
                    "success": False,
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        except MatlabEngineError as e:
            return Response(
                {
                    "detail": str(e),
                    "error_type": "MatlabEngineError",
                    "success": False,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            return Response(
                {
                    "detail": f"Unexpected error: {str(e)}",
                    "error_type": type(e).__name__,
                    "success": False,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BatchCalculatePcView(APIView):
    """Calculate Pc for multiple CDMs in batch.
    
    POST: Calculate Pc for a list of CDM IDs
    
    Request Body:
    {
        "cdm_ids": [1, 2, 3, 4, 5],
        "method": "multistep" | "circle" | "dilution",  // default: "multistep"
        "update_cdms": true | false  // default: true
    }
    
    Response:
    {
        "total": 5,
        "successful": 4,
        "failed": 1,
        "results": [
            {"cdm_id": 1, "Pc": 1.23e-5, "success": true, ...},
            {"cdm_id": 2, "Pc": 4.56e-6, "success": true, ...},
            ...
        ]
    }
    """
    
    def post(self, request, *args, **kwargs):
        """Calculate Pc for multiple CDMs."""
        # Extract parameters
        cdm_ids = request.data.get('cdm_ids', [])
        method = request.data.get('method', 'multistep').lower()
        update_cdms_flag = request.data.get('update_cdms', True)
        
        if not isinstance(cdm_ids, list) or not cdm_ids:
            return Response(
                {"detail": "cdm_ids must be a non-empty list of CDM IDs."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if method not in ['multistep', 'circle', 'dilution']:
            return Response(
                {"detail": f"Invalid method: {method}. Must be 'multistep', 'circle', or 'dilution'."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Fetch CDMs
        cdms = CDM.objects.filter(id__in=cdm_ids)
        
        if not cdms.exists():
            return Response(
                {"detail": "No CDMs found with the provided IDs."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate Pc for all CDMs
        try:
            results = batch_calculate_pc(list(cdms), method=method)
            
            # Update CDMs if requested
            if update_cdms_flag:
                for result in results:
                    if result.get('success'):
                        try:
                            cdm = CDM.objects.get(id=result['cdm_id'])
                            update_cdm_with_pc_result(cdm, result, save=True)
                            result['updated'] = True
                        except CDM.DoesNotExist:
                            result['updated'] = False
                    else:
                        result['updated'] = False
            
            # Count successes and failures
            successful = sum(1 for r in results if r.get('success'))
            failed = len(results) - successful
            
            return Response(
                {
                    "total": len(results),
                    "successful": successful,
                    "failed": failed,
                    "results": results,
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            return Response(
                {
                    "detail": f"Batch calculation failed: {str(e)}",
                    "error_type": type(e).__name__,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    
__all__ = [
    "api_index",
    "CDMListCreateView",
    "CDMDetailView",
    "SpaceObjectListCreateView",
    "EventListView",
    "CalculatePcView",
    "BatchCalculatePcView",
]