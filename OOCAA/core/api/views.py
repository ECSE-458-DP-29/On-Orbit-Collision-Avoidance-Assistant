"""API views for CDM and SpaceObject management."""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib import messages
from django.views.generic import View
import json

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
from core.services.cdm_service import parse_cdm_json


def api_index(request):
    """Render a small landing page for the API area."""
    return render(request, "api_index.html", {"message": "Core API landing page"})


def home(request):
    """Render the home page."""
    return render(request, "home.html")


def globe(request):
    """Render the 3D globe viewer page with satellite data from CDM.
    
    If multiple events exist, displays only the CDM with the latest creation_date for each event.
    If obj_id parameter is provided, filters CDMs to show only those containing that object.
    """
    from django.db.models import Max, Q
    
    # Get optional object_id parameter to filter for a specific object
    obj_id = request.GET.get('obj_id', None)
    
    # Group CDMs by event and get only the latest one for each event
    # Also filter by object if specified
    queryset = CDM.objects.filter(event__isnull=False)
    
    if obj_id:
        try:
            obj_id = int(obj_id)
            # Filter CDMs that include this object (either obj1 or obj2)
            queryset = queryset.filter(Q(obj1_id=obj_id) | Q(obj2_id=obj_id))
        except ValueError:
            pass
    
    # Get CDMs grouped by event with latest creation_date
    events_with_cdms = queryset.values('event_id').annotate(
        latest_creation_date=Max('creation_date')
    )
    
    # Collect CDMs: latest from each event + CDMs without events
    cdms = CDM.objects.filter(event__isnull=True)  # CDMs without events
    
    if obj_id:
        try:
            obj_id = int(obj_id)
            # Also filter CDMs without events by object
            cdms = cdms.filter(Q(obj1_id=obj_id) | Q(obj2_id=obj_id))
        except ValueError:
            pass
    
    for event_info in events_with_cdms:
        event_id = event_info['event_id']
        latest_date = event_info['latest_creation_date']
        # Get the CDM with latest creation_date for this event
        latest_cdm = CDM.objects.filter(
            event_id=event_id,
            creation_date=latest_date
        ).select_related('obj1', 'obj2').first()
        if latest_cdm:
            cdms = cdms | CDM.objects.filter(pk=latest_cdm.pk)
    
    # Ensure we have related objects
    cdms = cdms.select_related('obj1', 'obj2')
    
    # Serialize CDM data to JSON for JavaScript
    cdm_data = []
    for cdm in cdms:
        cdm_data.append({
            'cdm_id': cdm.cdm_id,
            'obj1_name': cdm.obj1.object_name if cdm.obj1 else 'Unknown',
            'obj1_id': cdm.obj1.id if cdm.obj1 else None,
            'obj1_x': cdm.obj1_position_x,
            'obj1_y': cdm.obj1_position_y,
            'obj1_z': cdm.obj1_position_z,
            'obj2_name': cdm.obj2.object_name if cdm.obj2 else 'Unknown',
            'obj2_id': cdm.obj2.id if cdm.obj2 else None,
            'obj2_x': cdm.obj2_position_x,
            'obj2_y': cdm.obj2_position_y,
            'obj2_z': cdm.obj2_position_z,
            'miss_distance_m': cdm.miss_distance_m,
            'collision_probability': float(cdm.collision_probability) if cdm.collision_probability else None,
        })
    context = {'cdms_json': json.dumps(cdm_data), 'selected_obj_id': obj_id}
    return render(request, "globe.html", context)


@login_required(login_url='/login/')
def view_cdm(request, pk):
    """Display detailed view of a specific CDM.
    
    GET: Display all attributes of a CDM
    """
    try:
        cdm = CDM.objects.get(pk=pk)
    except CDM.DoesNotExist:
        messages.error(request, "CDM not found.")
        return redirect('manage-cdms')
    
    # Get all CDM attributes
    context = {
        'cdm': cdm,
        'cdm_id': cdm.cdm_id,
        'obj1': cdm.obj1,
        'obj2': cdm.obj2,
        'event': cdm.event,
    }
    
    return render(request, 'view_cdm.html', context)


class CustomLogoutView(View):
    """Custom logout view that handles both GET and POST requests."""
    def get(self, request):
        logout(request)
        return redirect('home')
    
    def post(self, request):
        logout(request)
        return redirect('home')


def signup(request):
    """Handle user registration. New users get Observer role by default."""
    from django.contrib.auth import login
    from core.forms import SignupForm
    
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Your account has been created.')
            return redirect('home')
    else:
        form = SignupForm()
    
    return render(request, 'registration/signup.html', {'form': form})


@login_required(login_url='/login/')
def manage_cdms(request):
    """Manage CDMs page with filtering and pagination.
    
    GET: Display CDMs with filters and sorting
    POST: Handle delete actions via form submission
    """
    # Handle POST requests (delete actions)
    if request.method == 'POST':
        action = request.POST.get('action')
        cdm_id = request.POST.get('cdm_id')
        
        if action == 'delete' and cdm_id:
            try:
                cdm = CDM.objects.get(id=cdm_id)
                cdm_name = cdm.cdm_id
                cdm.delete()
                messages.success(request, f"CDM '{cdm_name}' deleted successfully.")
            except CDM.DoesNotExist:
                messages.error(request, "CDM not found.")
            except Exception as e:
                messages.error(request, f"Error deleting CDM: {str(e)}")
        
        return redirect('manage-cdms')
    
    # Handle GET requests (display and filter)
    cdms = CDM.objects.all().select_related('obj1', 'obj2', 'event')
    
    # Build filter parameters for display
    filters = {
        'simple_search': request.GET.get('simple_search', ''),
        'cdm_id': request.GET.get('cdm_id', ''),
        'obj1_id': request.GET.get('obj1_id', ''),
        'obj2_id': request.GET.get('obj2_id', ''),
        'event_id': request.GET.get('event_id', ''),
        'pc_min': request.GET.get('pc_min', ''),
        'pc_max': request.GET.get('pc_max', ''),
        'sort_field': request.GET.get('sort_field', 'creation_date'),
        'sort_order': request.GET.get('sort_order', 'desc'),
    }
    
    # Apply simple search first (searches CDM ID, Object Designators, and Object Names)
    if filters['simple_search']:
        search_term = filters['simple_search']
        from django.db.models import Q
        cdms = cdms.filter(
            Q(cdm_id__icontains=search_term) | 
            Q(obj1__object_designator__icontains=search_term) | 
            Q(obj2__object_designator__icontains=search_term) |
            Q(obj1__object_name__icontains=search_term) |
            Q(obj2__object_name__icontains=search_term)
        )
    
    # Apply advanced filters
    if filters['cdm_id']:
        cdms = cdms.filter(cdm_id__icontains=filters['cdm_id'])
    
    if filters['obj1_id']:
        cdms = cdms.filter(obj1__object_designator__icontains=filters['obj1_id'])
    
    if filters['obj2_id']:
        cdms = cdms.filter(obj2__object_designator__icontains=filters['obj2_id'])
    
    if filters['event_id']:
        try:
            event_id = int(filters['event_id'])
            cdms = cdms.filter(event_id=event_id)
        except ValueError:
            pass
    
    if filters['pc_min']:
        try:
            pc_min = float(filters['pc_min'])
            cdms = cdms.filter(collision_probability__gte=pc_min)
        except ValueError:
            pass
    
    if filters['pc_max']:
        try:
            pc_max = float(filters['pc_max'])
            cdms = cdms.filter(collision_probability__lte=pc_max)
        except ValueError:
            pass
    
    # Apply sorting
    # Define allowed fields for sorting
    allowed_sort_fields = [
        'creation_date', 'tca', 'collision_probability',
        'miss_distance_m', 'cdm_id', 'event_id', 'obj1_id', 'obj2_id'
    ]
    
    sort_field = filters['sort_field']
    sort_order = filters['sort_order']
    
    # Validate sort_field
    if sort_field not in allowed_sort_fields:
        sort_field = 'creation_date'
    
    # Validate sort_order
    if sort_order not in ['asc', 'desc']:
        sort_order = 'desc'
    
    # Build the order_by parameter
    if sort_order == 'asc':
        order_by_field = sort_field
    else:
        order_by_field = f'-{sort_field}'
    
    cdms = cdms.order_by(order_by_field)
    
    # Pagination
    paginator = Paginator(cdms, 25)  # 25 CDMs per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'cdms': page_obj.object_list,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'filters': filters,
    }
    
    return render(request, 'manage_cdms.html', context)


@login_required(login_url='/login/')
def upload_cdm(request):
    """Handle CDM file uploads.
    
    GET: Display upload form
    POST: Process uploaded file and create CDM(s)
    """
    if request.method == 'POST':
        uploaded_file = request.FILES.get('cdm_file')
        auto_calculate_pc = request.POST.get('auto_calculate_pc') == 'on'
        
        if not uploaded_file:
            messages.error(request, 'No file selected.')
            return redirect('upload-cdm')
        
        if not uploaded_file.name.endswith('.json'):
            messages.error(request, 'Please upload a JSON file.')
            return redirect('upload-cdm')
        
        try:
            # Read and parse JSON
            file_content = uploaded_file.read().decode('utf-8')
            data = json.loads(file_content)
            
            # Handle both single object and array of objects
            if isinstance(data, dict):
                data = [data]
            elif not isinstance(data, list):
                messages.error(request, 'Invalid JSON format. Expected object or array.')
                return redirect('upload-cdm')
            
            # Process each CDM in the file
            successful = 0
            failed = 0
            errors = []
            
            for idx, cdm_data in enumerate(data):
                try:
                    # Wrap in transaction for atomicity
                    from django.db import transaction
                    with transaction.atomic():
                        cdm, obj1, obj2 = parse_cdm_json(cdm_data)
                        successful += 1
                        
                        # Optionally calculate Pc
                        if auto_calculate_pc:
                            try:
                                result = calculate_pc_multistep(cdm, None)
                                if result.get('success'):
                                    update_cdm_with_pc_result(cdm, result, save=True)
                            except Exception as e:
                                # Don't fail the CDM upload if Pc calculation fails
                                messages.warning(request, f'CDM {cdm.cdm_id} uploaded but Pc calculation failed: {str(e)}')
                                
                except ValueError as e:
                    failed += 1
                    error_msg = f'CDM #{idx+1}: {str(e)}'
                    errors.append(error_msg)
                except Exception as e:
                    failed += 1
                    error_msg = f'CDM #{idx+1}: {str(e)}'
                    errors.append(error_msg)
            
            # Report results
            if successful > 0:
                msg = f'✓ Successfully uploaded {successful} CDM{"s" if successful != 1 else ""}.'
                if failed > 0:
                    msg += f' ✗ {failed} CDM{"s" if failed != 1 else ""} failed.'
                messages.success(request, msg)
                
                if errors:
                    for error in errors:
                        messages.warning(request, error)
            else:
                messages.error(request, f'✗ Failed to process any CDMs from the file.')
                if errors:
                    for error in errors:
                        messages.error(request, error)
            
            return redirect('manage-cdms')
            
        except json.JSONDecodeError as e:
            messages.error(request, f'Invalid JSON file: {str(e)}')
            return redirect('upload-cdm')
        except Exception as e:
            messages.error(request, f'Error processing file: {str(e)}')
            import traceback
            messages.error(request, f'Details: {traceback.format_exc()}')
            return redirect('upload-cdm')
    
    # GET request - show upload form
    return render(request, 'upload_cdm.html')


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
        
        if 'sort_field' in request.query_params:
            filters['sort_field'] = request.query_params['sort_field']
        
        if 'sort_order' in request.query_params:
            filters['sort_order'] = request.query_params['sort_order']
        
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
        
        if 'sort_field' in request.query_params:
            filters['sort_field'] = request.query_params['sort_field']
        
        if 'sort_order' in request.query_params:
            filters['sort_order'] = request.query_params['sort_order']
        
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
    "home",
    "globe",
    "view_cdm",
    "CustomLogoutView",
    "api_index",
    "manage_cdms",
    "upload_cdm",
    "CDMListCreateView",
    "CDMDetailView",
    "SpaceObjectListCreateView",
    "EventListView",
    "CalculatePcView",
    "BatchCalculatePcView",
    "ParseCDMJsonView",
]