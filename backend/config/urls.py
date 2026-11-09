from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Sprint 1 auth endpoints will be wired here:
    # path('api/v1/auth/', include('apps.users.api.v1.urls')),
    # Sprint 3 portfolio endpoints:
    # path('api/v1/portfolios/', include('apps.portfolios.api.v1.urls')),
]
