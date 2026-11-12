from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)

from core.health import HealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Health Check API v1
    path('api/v1/health/', HealthCheckView.as_view(), name='health-check'),

    # Authentication & User Profile API v1
    path('api/v1/auth/', include('apps.users.api.v1.urls')),
    path('api/v1/users/', include('apps.users.api.v1.urls_users')),

    # Dashboard API v1
    path('api/v1/dashboard/', include('apps.dashboard.api.v1.urls')),

    # Portfolios API v1
    path('api/v1/portfolios/', include('apps.portfolios.api.v1.urls')),

    # OpenAPI Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
