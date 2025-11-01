from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authtoken.models import Token
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import authenticate, get_user_model
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend

from .models import CDM, ManeuverPlan, CollisionAnalysis
from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    CDMSerializer,
    CDMListSerializer,
    ManeuverPlanSerializer,
    CollisionAnalysisSerializer,
    CollisionAnalysisDetailSerializer,
)

User = get_user_model()


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination for list views
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


# ============================================================================
# Authentication Endpoints
# ============================================================================

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Register a new user
    
    POST /api/register/
    Body: {
        "username": "string",
        "email": "string",
        "password": "string",
        "password_confirm": "string",
        "first_name": "string",
        "last_name": "string",
        "organization": "string",
        "role": "viewer|analyst|admin"
    }
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            'user': UserSerializer(user).data,
            'token': token.key,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Login user and return authentication token
    
    POST /api/login/
    Body: {
        "username": "string",
        "password": "string"
    }
    """
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response(
            {'error': 'Please provide both username and password'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = authenticate(username=username, password=password)
    
    if not user:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    token, created = Token.objects.get_or_create(user=user)
    
    return Response({
        'user': UserSerializer(user).data,
        'token': token.key,
        'message': 'Login successful'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Logout user and delete authentication token
    
    POST /api/logout/
    Headers: Authorization: Token <token>
    """
    try:
        request.user.auth_token.delete()
        return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_profile(request):
    """
    Get current user profile
    
    GET /api/profile/
    Headers: Authorization: Token <token>
    """
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


# ============================================================================
# CDM ViewSet
# ============================================================================

class CDMViewSet(viewsets.ModelViewSet):
    """
    ViewSet for CDM (Conjunction Data Message) operations
    
    list: GET /api/cdms/ - List all CDMs with filtering and pagination
    create: POST /api/cdms/ - Create a new CDM
    retrieve: GET /api/cdms/{id}/ - Get a specific CDM by ID
    update: PUT /api/cdms/{id}/ - Update a CDM
    partial_update: PATCH /api/cdms/{id}/ - Partially update a CDM
    destroy: DELETE /api/cdms/{id}/ - Delete a CDM
    """
    queryset = CDM.objects.all()
    serializer_class = CDMSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    
    # Filtering
    filterset_fields = ['status', 'risk_level', 'originator', 'created_by']
    
    # Searching
    search_fields = ['cdm_id', 'object1_name', 'object2_name', 'message_id']
    
    # Ordering
    ordering_fields = ['tca', 'created_at', 'collision_probability', 'miss_distance']
    ordering = ['-tca']

    def get_serializer_class(self):
        """Use lightweight serializer for list view"""
        if self.action == 'list':
            return CDMListSerializer
        return CDMSerializer

    def perform_create(self, serializer):
        """Set created_by user when creating a CDM"""
        serializer.save(created_by=self.request.user)

    def perform_update(self, serializer):
        """Set updated_by user when updating a CDM"""
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def by_cdm_id(self, request):
        """
        Get CDM by CDM ID (custom identifier)
        
        GET /api/cdms/by_cdm_id/?cdm_id=<cdm_id>
        """
        cdm_id = request.query_params.get('cdm_id', None)
        if not cdm_id:
            return Response(
                {'error': 'cdm_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            cdm = CDM.objects.get(cdm_id=cdm_id)
            serializer = CDMSerializer(cdm)
            return Response(serializer.data)
        except CDM.DoesNotExist:
            return Response(
                {'error': f'CDM with cdm_id {cdm_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=False, methods=['get'])
    def high_risk(self, request):
        """
        Get all high and critical risk CDMs
        
        GET /api/cdms/high_risk/
        """
        high_risk_cdms = self.queryset.filter(risk_level__in=['high', 'critical'])
        page = self.paginate_queryset(high_risk_cdms)
        if page is not None:
            serializer = CDMListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = CDMListSerializer(high_risk_cdms, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """
        Get upcoming conjunctions (TCA in the future)
        
        GET /api/cdms/upcoming/
        """
        from django.utils import timezone
        upcoming_cdms = self.queryset.filter(tca__gte=timezone.now())
        page = self.paginate_queryset(upcoming_cdms)
        if page is not None:
            serializer = CDMListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = CDMListSerializer(upcoming_cdms, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def maneuvers(self, request, pk=None):
        """
        Get all maneuver plans for a specific CDM
        
        GET /api/cdms/{id}/maneuvers/
        """
        cdm = self.get_object()
        maneuvers = cdm.maneuver_plans.all()
        serializer = ManeuverPlanSerializer(maneuvers, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        """
        Update CDM status
        
        POST /api/cdms/{id}/update_status/
        Body: {"status": "received|analyzing|analyzed|maneuver_planned|maneuver_executed|passed|false_alarm"}
        """
        cdm = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response(
                {'error': 'status field is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        valid_statuses = ['received', 'analyzing', 'analyzed', 'maneuver_planned', 
                         'maneuver_executed', 'passed', 'false_alarm']
        
        if new_status not in valid_statuses:
            return Response(
                {'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        cdm.status = new_status
        cdm.updated_by = request.user
        cdm.save()
        
        serializer = CDMSerializer(cdm)
        return Response(serializer.data)


# ============================================================================
# Maneuver Plan ViewSet
# ============================================================================

class ManeuverPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Maneuver Plan operations
    
    list: GET /api/maneuvers/ - List all maneuver plans
    create: POST /api/maneuvers/ - Create a new maneuver plan
    retrieve: GET /api/maneuvers/{id}/ - Get a specific maneuver plan
    update: PUT /api/maneuvers/{id}/ - Update a maneuver plan
    partial_update: PATCH /api/maneuvers/{id}/ - Partially update a maneuver plan
    destroy: DELETE /api/maneuvers/{id}/ - Delete a maneuver plan
    """
    queryset = ManeuverPlan.objects.all()
    serializer_class = ManeuverPlanSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    
    filterset_fields = ['status', 'maneuver_type', 'cdm']
    ordering_fields = ['maneuver_time', 'created_at', 'fuel_cost']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        """Set created_by user when creating a maneuver plan"""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """
        Approve a maneuver plan
        
        POST /api/maneuvers/{id}/approve/
        """
        maneuver = self.get_object()
        maneuver.status = 'approved'
        maneuver.save()
        serializer = ManeuverPlanSerializer(maneuver)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """
        Reject a maneuver plan
        
        POST /api/maneuvers/{id}/reject/
        Body (optional): {"notes": "reason for rejection"}
        """
        maneuver = self.get_object()
        maneuver.status = 'rejected'
        notes = request.data.get('notes')
        if notes:
            maneuver.notes = notes
        maneuver.save()
        serializer = ManeuverPlanSerializer(maneuver)
        return Response(serializer.data)


# ============================================================================
# Collision Analysis ViewSet
# ============================================================================

class CollisionAnalysisViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Collision Analysis operations
    
    list: GET /api/analyses/ - List all collision analyses
    create: POST /api/analyses/ - Create a new collision analysis
    retrieve: GET /api/analyses/{id}/ - Get a specific collision analysis
    update: PUT /api/analyses/{id}/ - Update a collision analysis
    partial_update: PATCH /api/analyses/{id}/ - Partially update a collision analysis
    destroy: DELETE /api/analyses/{id}/ - Delete a collision analysis
    """
    queryset = CollisionAnalysis.objects.all()
    serializer_class = CollisionAnalysisSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    
    filterset_fields = ['recommended_action', 'performed_by']
    ordering_fields = ['performed_at', 'combined_risk_score']
    ordering = ['-performed_at']

    def get_serializer_class(self):
        """Use detailed serializer for retrieve view"""
        if self.action == 'retrieve':
            return CollisionAnalysisDetailSerializer
        return CollisionAnalysisSerializer

    def perform_create(self, serializer):
        """Set performed_by user when creating an analysis"""
        serializer.save(performed_by=self.request.user)

    @action(detail=False, methods=['post'])
    def analyze_collision(self, request):
        """
        Perform collision analysis on multiple CDMs
        
        POST /api/analyses/analyze_collision/
        Body: {
            "cdm_ids": ["CDM001", "CDM002"],
            "analysis_method": "string",
            "time_window_start": "datetime",
            "time_window_end": "datetime"
        }
        """
        cdm_ids = request.data.get('cdm_ids', [])
        
        if not cdm_ids or len(cdm_ids) < 2:
            return Response(
                {'error': 'At least 2 CDM IDs are required for collision analysis'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Fetch CDMs
        cdms = CDM.objects.filter(cdm_id__in=cdm_ids)
        
        if cdms.count() != len(cdm_ids):
            return Response(
                {'error': 'One or more CDM IDs not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate combined risk (simplified example)
        total_collision_prob = sum(cdm.collision_probability for cdm in cdms)
        avg_collision_prob = total_collision_prob / len(cdms)
        
        # Determine recommendation based on risk
        if avg_collision_prob > 0.0001:
            recommended_action = 'maneuver'
            recommendation = f'High collision risk detected. Average probability: {avg_collision_prob:.6f}. Recommend immediate maneuver planning.'
        elif avg_collision_prob > 0.00001:
            recommended_action = 'monitor'
            recommendation = f'Moderate collision risk detected. Average probability: {avg_collision_prob:.6f}. Recommend continued monitoring.'
        else:
            recommended_action = 'no_action'
            recommendation = f'Low collision risk detected. Average probability: {avg_collision_prob:.6f}. No immediate action required.'
        
        # Create analysis record
        analysis_data = {
            'analysis_id': f'ANALYSIS_{cdms.first().cdm_id}_{len(CollisionAnalysis.objects.all()) + 1}',
            'analysis_method': request.data.get('analysis_method', 'Combined Probability Analysis'),
            'time_window_start': request.data.get('time_window_start', cdms.order_by('tca').first().tca),
            'time_window_end': request.data.get('time_window_end', cdms.order_by('-tca').first().tca),
            'combined_risk_score': avg_collision_prob,
            'recommendation': recommendation,
            'recommended_action': recommended_action,
        }
        
        serializer = CollisionAnalysisSerializer(data=analysis_data)
        
        if serializer.is_valid():
            analysis = serializer.save(performed_by=request.user)
            analysis.cdms.set(cdms)
            
            return Response(
                CollisionAnalysisDetailSerializer(analysis).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ============================================================================
# Statistics and Dashboard Endpoints
# ============================================================================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """
    Get dashboard statistics
    
    GET /api/dashboard/stats/
    """
    from django.utils import timezone
    from django.db.models import Count, Avg
    
    total_cdms = CDM.objects.count()
    high_risk_count = CDM.objects.filter(risk_level__in=['high', 'critical']).count()
    upcoming_conjunctions = CDM.objects.filter(tca__gte=timezone.now()).count()
    
    status_breakdown = CDM.objects.values('status').annotate(count=Count('id'))
    risk_breakdown = CDM.objects.values('risk_level').annotate(count=Count('id'))
    
    avg_collision_prob = CDM.objects.aggregate(avg_prob=Avg('collision_probability'))
    
    stats = {
        'total_cdms': total_cdms,
        'high_risk_cdms': high_risk_count,
        'upcoming_conjunctions': upcoming_conjunctions,
        'status_breakdown': list(status_breakdown),
        'risk_breakdown': list(risk_breakdown),
        'average_collision_probability': avg_collision_prob['avg_prob'] or 0,
        'total_maneuver_plans': ManeuverPlan.objects.count(),
        'total_analyses': CollisionAnalysis.objects.count(),
    }
    
    return Response(stats)

