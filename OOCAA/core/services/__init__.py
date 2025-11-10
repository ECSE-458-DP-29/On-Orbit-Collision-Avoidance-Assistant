"""Service package for core app.

Keep service factories / layer entrypoints here.
"""

from .cdm_service import create_cdm

__all__ = ["create_cdm"]
