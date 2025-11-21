"""Service package for core app.

Keep service factories / layer entrypoints here.
"""

# Re-export commonly-used service functions from submodules so callers
# can import them from `core.services` (e.g. `from core.services import get_cdm`).
from .cdm_service import (
	create_cdm,
	get_cdm,
	list_cdms,
	update_cdm,
	delete_cdm,
	assign_cdm_to_event,
	regroup_all_cdms,
    list_events,
)

__all__ = [
	"create_cdm",
	"get_cdm",
	"list_cdms",
	"update_cdm",
	"delete_cdm",
	"assign_cdm_to_event",
	"regroup_all_cdms",
    "list_events",
]
