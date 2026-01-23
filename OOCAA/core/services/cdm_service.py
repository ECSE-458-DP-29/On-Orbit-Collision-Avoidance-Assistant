"""Service layer for CDM-related business logic.

Keep creation/auxiliary logic here so views/controllers stay thin.
"""
from typing import Any, Dict, Optional
from datetime import timedelta

from django.db import transaction
from django.core.exceptions import ValidationError

from core.models.cdm import CDM
from core.models.event import Event
from core.models.spaceobject import SpaceObject


@transaction.atomic
def create_cdm(validated_data: Dict[str, Any]) -> CDM:
    """Create and return a CDM.

    Assumes `validated_data` comes from a DRF serializer which has
    already resolved related PKs into model instances (or None). We
    perform a small business-rule check (e.g., obj1 != obj2) and then
    persist the CDM.
    
    After creation, the CDM is automatically assigned to an event.
    """
    data = validated_data.copy()

    # If nested creation data was provided (obj1_data / obj2_data), create or
    # get the corresponding SpaceObject instances. This makes the API
    # convenient for clients that don't want to create SpaceObjects first.
    for nested_key, fk_key in (('obj1_data', 'obj1'), ('obj2_data', 'obj2')):
        nested = data.pop(nested_key, None)
        if nested is None:
            continue
        # If the caller provided object_designator, prefer get_or_create by it
        designator = nested.get('object_designator') if isinstance(nested, dict) else None
        if designator:
            obj, _ = SpaceObject.objects.get_or_create(
                object_designator=designator, defaults=nested
            )
        else:
            # No unique designator given; create a new object with supplied fields
            obj = SpaceObject.objects.create(**nested)
        data[fk_key] = obj

    # Defensive checks: ensure obj1/obj2 are either SpaceObject instances or None
    for key in ('obj1', 'obj2'):
        val = data.get(key)
        if val is not None and not isinstance(val, SpaceObject):
            raise ValueError(f"{key} must be a SpaceObject instance or None")

    # Business rule example: prevent the same object referenced twice
    if data.get('obj1') is not None and data.get('obj1') == data.get('obj2'):
        raise ValueError("obj1 and obj2 must be different SpaceObject instances")

    cdm = CDM.objects.create(**data)
    
    # Automatically assign to event after creation
    assign_cdm_to_event(cdm)
    
    return cdm


def get_cdm(cdm_id: int) -> Optional[CDM]:
    """Retrieve a CDM by its ID.
    
    Args:
        cdm_id: The primary key of the CDM to retrieve
        
    Returns:
        CDM instance if found, None otherwise
    """
    try:
        return CDM.objects.select_related('obj1', 'obj2', 'event').get(id=cdm_id)
    except CDM.DoesNotExist:
        return None


def list_cdms(filters: Optional[Dict[str, Any]] = None) -> 'QuerySet[CDM]':
    """List all CDMs with optional filtering.
    
    Args:
        filters: Optional dictionary of filter parameters
            - obj1_id: Filter by primary object ID
            - obj2_id: Filter by secondary object ID
            - event_id: Filter by event ID
            - tca_after: Filter CDMs with TCA after this datetime
            - tca_before: Filter CDMs with TCA before this datetime
            - min_collision_probability: Filter by minimum collision probability
            
    Returns:
        QuerySet of CDM instances
    """
    queryset = CDM.objects.select_related('obj1', 'obj2', 'event').all()
    
    if not filters:
        return queryset
    
    # Apply filters if provided
    if 'obj1_id' in filters:
        queryset = queryset.filter(obj1_id=filters['obj1_id'])
    
    if 'obj2_id' in filters:
        queryset = queryset.filter(obj2_id=filters['obj2_id'])
    
    if 'event_id' in filters:
        queryset = queryset.filter(event_id=filters['event_id'])
    
    if 'tca_after' in filters:
        queryset = queryset.filter(tca__gte=filters['tca_after'])
    
    if 'tca_before' in filters:
        queryset = queryset.filter(tca__lte=filters['tca_before'])
    
    if 'min_collision_probability' in filters:
        queryset = queryset.filter(
            collision_probability__gte=filters['min_collision_probability']
        )
    
    return queryset.order_by('-tca')


@transaction.atomic
def update_cdm(cdm_id: int, validated_data: Dict[str, Any]) -> Optional[CDM]:
    """Update an existing CDM.
    
    Args:
        cdm_id: The primary key of the CDM to update
        validated_data: Dictionary of validated fields to update
        
    Returns:
        Updated CDM instance if found, None otherwise
        
    Raises:
        ValueError: If update violates business rules
        
    """
    cdm = get_cdm(cdm_id)
    if not cdm:
        return None
    
    data = validated_data.copy()
    
    # Remove read-only fields that shouldn't be updated
    data.pop('obj1_data', None)
    data.pop('obj2_data', None)
    data.pop('event', None)  # Event assignment is automatic
    
    # Validate obj1 != obj2 if either is being changed
    new_obj1 = data.get('obj1', cdm.obj1)
    new_obj2 = data.get('obj2', cdm.obj2)
    
    if new_obj1 is not None and new_obj1 == new_obj2:
        raise ValueError("obj1 and obj2 must be different SpaceObject instances")
    
    # Track if objects or TCA changed (affects event assignment)
    objects_changed = 'obj1' in data or 'obj2' in data
    tca_changed = 'tca' in data
    
    # Store the old event before making changes (for cleanup)
    old_event = cdm.event
    
    # Update fields
    for field, value in data.items():
        setattr(cdm, field, value)
    
    cdm.full_clean()  # Validate model constraints
    cdm.save()
    
    # Re-assign to event if objects or TCA changed
    if objects_changed or tca_changed:
        if cdm.obj1 and cdm.obj2:
            assign_cdm_to_event(cdm)
    
    # Clean up orphaned events
    if old_event and old_event != cdm.event:
        _cleanup_orphaned_event(old_event)
    
    return cdm


def _cleanup_orphaned_event(event: Event) -> None:
    """Delete an event if it has no associated CDMs.
    
    Args:
        event: The Event instance to check and potentially delete
        
    """
    # Refresh from database to get current CDM count
    event.refresh_from_db()
    
    if event.cdms.count() == 0:
        event.delete()


@transaction.atomic
def delete_cdm(cdm_id: int) -> bool:
    """Delete a CDM by its ID.
    
    Args:
        cdm_id: The primary key of the CDM to delete
        
    Returns:
        True if CDM was deleted, False if not found

    """
    cdm = get_cdm(cdm_id)
    if not cdm:
        return False
    
    # Store the event before deleting the CDM
    event = cdm.event
    
    cdm.delete()
    
    # Clean up orphaned event if it exists
    if event:
        _cleanup_orphaned_event(event)
    
    return True


@transaction.atomic
def assign_cdm_to_event(cdm: CDM, tca_threshold_seconds: int = 10) -> Event:
    """Assign a CDM to an existing event or create a new one.
    
    Args:
        cdm: The CDM instance to assign
        tca_threshold_seconds: Maximum time difference in seconds to consider
                              CDMs part of the same event (default: 10)
    
    Returns:
        The Event instance the CDM was assigned to
        
    Raises:
        ValueError: If CDM is missing obj1 or obj2

    """
    if not cdm.obj1 or not cdm.obj2:
        raise ValueError("CDM must have both obj1 and obj2 to be assigned to an event")
    
    # Normalize object pair order (always store lower ID first)
    obj1, obj2 = _normalize_object_pair(cdm.obj1, cdm.obj2)
    
    # Look for existing events with the same object pair and nearby TCA
    tca_threshold = timedelta(seconds=tca_threshold_seconds)
    tca_min = cdm.tca - tca_threshold
    tca_max = cdm.tca + tca_threshold
    
    matching_event = Event.objects.filter(
        obj1=obj1,
        obj2=obj2,
        representative_tca__gte=tca_min,
        representative_tca__lte=tca_max,
    ).first()
    
    if matching_event:
        # Assign to existing event
        cdm.event = matching_event
        cdm.save(update_fields=['event'])
        return matching_event
    else:
        # Create new event
        event = Event.objects.create(
            obj1=obj1,
            obj2=obj2,
            representative_tca=cdm.tca,
        )
        cdm.event = event
        cdm.save(update_fields=['event'])
        return event


@transaction.atomic
def regroup_all_cdms(tca_threshold_seconds: int = 10) -> Dict[str, int]:
    """Regroup all CDMs into events, clearing existing assignments.
    
    Useful for:
    - Initial migration when adding the Event model
    - Fixing grouping issues
    - Changing the TCA threshold
    
    Args:
        tca_threshold_seconds: Maximum time difference in seconds
    
    Returns:
        Dictionary with statistics: 
        {'processed': int, 'events_created': int, 'events_updated': int}
    """
    # Clear all existing event assignments
    CDM.objects.all().update(event=None)
    
    # Delete all events (they'll be recreated)
    Event.objects.all().delete()
    
    # Process all CDMs
    cdms = CDM.objects.filter(
        obj1__isnull=False, 
        obj2__isnull=False
    ).select_related('obj1', 'obj2').order_by('tca')
    
    stats = {
        'processed': 0,
        'events_created': 0,
        'skipped': 0,
    }
    
    events_before = Event.objects.count()
    
    for cdm in cdms:
        try:
            event = assign_cdm_to_event(cdm, tca_threshold_seconds)
            stats['processed'] += 1
        except ValueError:
            stats['skipped'] += 1
    
    stats['events_created'] = Event.objects.count() - events_before
    
    return stats


def _normalize_object_pair(obj1: SpaceObject, obj2: SpaceObject) -> tuple[SpaceObject, SpaceObject]:
    """Return objects in consistent order (lower ID first).
    
    This ensures (A, B) and (B, A) are treated as the same pair,
    preventing duplicate events.
    """
    if obj1.id < obj2.id:
        return obj1, obj2
    return obj2, obj1


def list_events(filters: Optional[Dict[str, Any]] = None) -> 'QuerySet[Event]':
    """List all events with optional filtering.
    
    Args:
        filters: Optional dictionary of filter parameters
            - object_id: Filter by object ID (matches if object is either obj1 or obj2)
            - tca_after: Filter events with representative TCA after this datetime
            - tca_before: Filter events with representative TCA before this datetime
            - min_cdm_count: Filter events with at least this many CDMs
            
    Returns:
        QuerySet of Event instances
        
    """
    from django.db.models import Count, Q
    
    queryset = Event.objects.select_related('obj1', 'obj2').prefetch_related('cdms').all()
    
    if not filters:
        return queryset
    
    # Apply filters if provided
    if 'object_id' in filters:
        # Filter where the object appears in EITHER obj1 or obj2 position
        object_id = filters['object_id']
        queryset = queryset.filter(Q(obj1_id=object_id) | Q(obj2_id=object_id))
    
    if 'tca_after' in filters:
        queryset = queryset.filter(representative_tca__gte=filters['tca_after'])
    
    if 'tca_before' in filters:
        queryset = queryset.filter(representative_tca__lte=filters['tca_before'])
    
    if 'min_cdm_count' in filters:
        queryset = queryset.annotate(cdm_count=Count('cdms')).filter(
            cdm_count__gte=filters['min_cdm_count']
        )
    
    return queryset.order_by('-representative_tca')

def parse_cdm_json(data: dict) -> CDM:
    """Parse a JSON CDM dictionary and create a CDM object."""

    # Create or fetch SpaceObject 1
    obj1, created1 = SpaceObject.objects.get_or_create(
        object_designator=data.get("SAT1_OBJECT_DESIGNATOR"),
        defaults={
            "object_name": data.get("SAT1_OBJECT_NAME"),
            "object_type": data.get("SAT1_OBJECT_TYPE"),
            "operator_organization": data.get("SAT1_OPERATOR_ORGANIZATION"),
            "maneuverable": data.get("SAT1_MANEUVERABLE") == "YES",
        },
    )
    if created1:
        obj1.save()  # Explicitly save the object if it was newly created

    # Create or fetch SpaceObject 2
    obj2, created2 = SpaceObject.objects.get_or_create(
        object_designator=data.get("SAT2_OBJECT_DESIGNATOR"),
        defaults={
            "object_name": data.get("SAT2_OBJECT_NAME"),
            "object_type": data.get("SAT2_OBJECT_TYPE"),
            "operator_organization": data.get("SAT2_OPERATOR_ORGANIZATION"),
            "maneuverable": data.get("SAT2_MANEUVERABLE") == "YES",
        },
    )
    if created2:
        obj2.save()  # Explicitly save the object if it was newly created

    # Create the CDM object
    # Build covariance matrices
    obj1_cov = [
        [float(data.get("SAT1_CR_R", 0)), float(data.get("SAT1_CT_R", 0)), float(data.get("SAT1_CN_R", 0)), float(data.get("SAT1_CRDOT_R", 0)), float(data.get("SAT1_CTDOT_R", 0)), float(data.get("SAT1_CNDOT_R", 0))],
        [float(data.get("SAT1_CT_R", 0)), float(data.get("SAT1_CT_T", 0)), float(data.get("SAT1_CN_T", 0)), float(data.get("SAT1_CRDOT_T", 0)), float(data.get("SAT1_CTDOT_T", 0)), float(data.get("SAT1_CNDOT_T", 0))],
        [float(data.get("SAT1_CN_R", 0)), float(data.get("SAT1_CN_T", 0)), float(data.get("SAT1_CN_N", 0)), float(data.get("SAT1_CRDOT_N", 0)), float(data.get("SAT1_CTDOT_N", 0)), float(data.get("SAT1_CNDOT_N", 0))],
        [float(data.get("SAT1_CRDOT_R", 0)), float(data.get("SAT1_CRDOT_T", 0)), float(data.get("SAT1_CRDOT_N", 0)), float(data.get("SAT1_CRDOT_RDOT", 0)), float(data.get("SAT1_CTDOT_RDOT", 0)), float(data.get("SAT1_CNDOT_RDOT", 0))],
        [float(data.get("SAT1_CTDOT_R", 0)), float(data.get("SAT1_CTDOT_T", 0)), float(data.get("SAT1_CTDOT_N", 0)), float(data.get("SAT1_CTDOT_RDOT", 0)), float(data.get("SAT1_CTDOT_TDOT", 0)), float(data.get("SAT1_CNDOT_TDOT", 0))],
        [float(data.get("SAT1_CNDOT_R", 0)), float(data.get("SAT1_CNDOT_T", 0)), float(data.get("SAT1_CNDOT_N", 0)), float(data.get("SAT1_CNDOT_RDOT", 0)), float(data.get("SAT1_CNDOT_TDOT", 0)), float(data.get("SAT1_CNDOT_NDOT", 0))]
    ]
    obj2_cov = [
        [float(data.get("SAT2_CR_R", 0)), float(data.get("SAT2_CT_R", 0)), float(data.get("SAT2_CN_R", 0)), float(data.get("SAT2_CRDOT_R", 0)), float(data.get("SAT2_CTDOT_R", 0)), float(data.get("SAT2_CNDOT_R", 0))],
        [float(data.get("SAT2_CT_R", 0)), float(data.get("SAT2_CT_T", 0)), float(data.get("SAT2_CN_T", 0)), float(data.get("SAT2_CRDOT_T", 0)), float(data.get("SAT2_CTDOT_T", 0)), float(data.get("SAT2_CNDOT_T", 0))],
        [float(data.get("SAT2_CN_R", 0)), float(data.get("SAT2_CN_T", 0)), float(data.get("SAT2_CN_N", 0)), float(data.get("SAT2_CRDOT_N", 0)), float(data.get("SAT2_CTDOT_N", 0)), float(data.get("SAT2_CNDOT_N", 0))],
        [float(data.get("SAT2_CRDOT_R", 0)), float(data.get("SAT2_CRDOT_T", 0)), float(data.get("SAT2_CRDOT_N", 0)), float(data.get("SAT2_CRDOT_RDOT", 0)), float(data.get("SAT2_CTDOT_RDOT", 0)), float(data.get("SAT2_CNDOT_RDOT", 0))],
        [float(data.get("SAT2_CTDOT_R", 0)), float(data.get("SAT2_CTDOT_T", 0)), float(data.get("SAT2_CTDOT_N", 0)), float(data.get("SAT2_CTDOT_RDOT", 0)), float(data.get("SAT2_CTDOT_TDOT", 0)), float(data.get("SAT2_CNDOT_TDOT", 0))],
        [float(data.get("SAT2_CNDOT_R", 0)), float(data.get("SAT2_CNDOT_T", 0)), float(data.get("SAT2_CNDOT_N", 0)), float(data.get("SAT2_CNDOT_RDOT", 0)), float(data.get("SAT2_CNDOT_TDOT", 0)), float(data.get("SAT2_CNDOT_NDOT", 0))]
    ]

    cdm = CDM.objects.create(
        cdm_id=data.get("CDM_ID"),
        message_id=data.get("MESSAGE_ID"),
        creation_date=data.get("CREATION_DATE"),
        insert_epoch=data.get("INSERT_EPOCH"),
        ccsds_version=data.get("CCSDS_CDM_VERS"),
        originator=data.get("ORIGINATOR"),
        obj1=obj1,
        obj2=obj2,
        # Flat fields for positions and velocities
        obj1_position_x=float(data.get("SAT1_X")),
        obj1_position_y=float(data.get("SAT1_Y")),
        obj1_position_z=float(data.get("SAT1_Z")),
        obj1_velocity_x=float(data.get("SAT1_X_DOT")),
        obj1_velocity_y=float(data.get("SAT1_Y_DOT")),
        obj1_velocity_z=float(data.get("SAT1_Z_DOT")),
        obj2_position_x=float(data.get("SAT2_X")),
        obj2_position_y=float(data.get("SAT2_Y")),
        obj2_position_z=float(data.get("SAT2_Z")),
        obj2_velocity_x=float(data.get("SAT2_X_DOT")),
        obj2_velocity_y=float(data.get("SAT2_Y_DOT")),
        obj2_velocity_z=float(data.get("SAT2_Z_DOT")),
        # Covariance matrices
        obj1_covariance_matrix=obj1_cov,
        obj2_covariance_matrix=obj2_cov,
        # Hard body radius (default if not provided)
        hard_body_radius=float(data.get("HARD_BODY_RADIUS", 0.01)),
        state_vector_obj1={
            "x_km": data.get("SAT1_X"),
            "y_km": data.get("SAT1_Y"),
            "z_km": data.get("SAT1_Z"),
            "xdot_kms": data.get("SAT1_X_DOT"),
            "ydot_kms": data.get("SAT1_Y_DOT"),
            "zdot_kms": data.get("SAT1_Z_DOT"),
        },
        state_vector_obj2={
            "x_km": data.get("SAT2_X"),
            "y_km": data.get("SAT2_Y"),
            "z_km": data.get("SAT2_Z"),
            "xdot_kms": data.get("SAT2_X_DOT"),
            "ydot_kms": data.get("SAT2_Y_DOT"),
            "zdot_kms": data.get("SAT2_Z_DOT"),
        },
        physical_parameters_obj1={
            "area_pc": data.get("SAT1_AREA_PC"),
            "cd_area_mass": data.get("SAT1_CD_AREA_OVER_MASS"),
            "cr_area_mass": data.get("SAT1_CR_AREA_OVER_MASS"),
        },
        physical_parameters_obj2={
            "area_pc": data.get("SAT2_AREA_PC"),
            "cd_area_mass": data.get("SAT2_CD_AREA_OVER_MASS"),
            "cr_area_mass": data.get("SAT2_CR_AREA_OVER_MASS"),
        },
        tca=data.get("TCA"),
        miss_distance_m=data.get("MISS_DISTANCE"),
        relative_speed_ms=data.get("RELATIVE_SPEED"),
        relative_position={
            "r": data.get("RELATIVE_POSITION_R"),
            "t": data.get("RELATIVE_POSITION_T"),
            "n": data.get("RELATIVE_POSITION_N"),
        },
        relative_velocity={
            "r": data.get("RELATIVE_VELOCITY_R"),
            "t": data.get("RELATIVE_VELOCITY_T"),
            "n": data.get("RELATIVE_VELOCITY_N"),
        },
        collision_probability=data.get("COLLISION_PROBABILITY"),
        collision_probability_method=data.get("COLLISION_PROBABILITY_METHOD"),
        comments={
            "screening_option": data.get("COMMENT_SCREENING_OPTION"),
            "effective_hbr": data.get("COMMENT_EFFECTIVE_HBR"),
        },
    )
    cdm.save()  # Explicitly save the CDM object

    return cdm, obj1, obj2

__all__ = [
    'create_cdm',
    'get_cdm',
    'list_cdms',
    'update_cdm',
    'delete_cdm',
    'assign_cdm_to_event',
    'regroup_all_cdms',
    'list_events',
    'parse_cdm_json',
]
