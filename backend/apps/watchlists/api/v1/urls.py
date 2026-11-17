from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.watchlists.api.v1.views import WatchlistViewSet

router = DefaultRouter()
router.register(r'', WatchlistViewSet, basename='watchlist')

urlpatterns = [
    path('', include(router.urls)),
]
