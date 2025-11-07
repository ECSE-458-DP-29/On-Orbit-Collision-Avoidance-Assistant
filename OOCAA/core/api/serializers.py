"""Skeleton serializers for the core API.

Fill these in with DRF serializers when you decide to enable DRF.
"""

# Example placeholder imports; remove or replace with real DRF serializers
try:
    from rest_framework import serializers  # type: ignore
except Exception:
    # DRF not installed yet; provide lightweight fallback for type checks
    serializers = None


__all__ = [
    'serializers',
]
