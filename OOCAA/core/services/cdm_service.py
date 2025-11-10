"""Service layer for CDM-related business logic.

Keep creation/auxiliary logic here so views/controllers stay thin.
"""
from typing import Any, Dict

from core.models.cdm import CDM
from core.models.spaceobject import SpaceObject


def create_cdm(validated_data: Dict[str, Any]) -> CDM:
    """Create and return a CDM.

    Assumes `validated_data` comes from a DRF serializer which has
    already resolved related PKs into model instances (or None). We
    perform a small business-rule check (e.g., obj1 != obj2) and then
    persist the CDM.
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
    return cdm


__all__ = ['create_cdm']
