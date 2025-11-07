"""Simple, non-DRF views for the `core.api` package.

This file provides a tiny render-based view so visiting `/api/` can
show an informational HTML page before you wire full API endpoints.
"""
from django.shortcuts import render

#THis is an example view
def api_index(request):
    """Render a small landing page for the API area."""
    return render(request, "api_index.html", {"message": "Core API landing page"}) 


__all__ = ["api_index"]
