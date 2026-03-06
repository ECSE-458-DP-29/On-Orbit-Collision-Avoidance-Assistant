"""
URL configuration for OOCAA project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path, include
from core.api.views import home, signup
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView
from two_factor.urls import urlpatterns as tf_urls

urlpatterns = [
    path('', home, name='home'),  # Home page at root
    path('', include('core.api.urls')),  # Include all core.api.urls at root level (no /api/ prefix)
    
    path('admin/', admin.site.urls),
    
    # Swagger and OpenAPI documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/docs/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc-ui'),
    
    # Two-Factor Authentication URLs
    path('', include(tf_urls)),  # /account/login/, /account/two_factor/setup/, etc.
    
    # Logout (not included in two_factor)
    path('logout/', LogoutView.as_view(next_page='/'), name='logout'),
    
    # Custom signup (not handled by two_factor)
    path('signup/', signup, name='signup'),
]
