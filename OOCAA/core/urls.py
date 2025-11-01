from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for viewsets
router = DefaultRouter()
router.register(r'cdms', views.CDMViewSet, basename='cdm')
router.register(r'maneuvers', views.ManeuverPlanViewSet, basename='maneuver')
router.register(r'analyses', views.CollisionAnalysisViewSet, basename='analysis')

# URL patterns
urlpatterns = [
    # Authentication endpoints
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('profile/', views.user_profile, name='user-profile'),
    
    # Dashboard
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    
    # Include router URLs (CDMs, Maneuvers, Analyses)
    path('', include(router.urls)),
]
