"""Service layer for CDM-related business logic.

Keep creation/auxiliary logic here so views/controllers stay thin.
"""
from typing import Any, Dict
from datetime import timedelta

from django.db import transaction

from core.models.cdm import CDM
from core.models.event import Event
from core.models.spaceobject import SpaceObject


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


__all__ = ['create_cdm', 'assign_cdm_to_event', 'regroup_all_cdms']