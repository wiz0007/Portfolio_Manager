from django.urls import include, path
from rest_framework.routers import DefaultRouter

from apps.market_data.api.v1.views import (
    InstrumentViewSet,
    MarketDataHealthView,
    MarketDataHistoryView,
    MarketDataOverviewView,
    MarketDataProvidersView,
    MarketDataQuoteView,
    MarketDataRefreshView,
)

router = DefaultRouter()
router.register(r'instruments', InstrumentViewSet, basename='instrument')

urlpatterns = [
    # Instruments router endpoints (/api/v1/instruments/, /api/v1/instruments/search/)
    path('', include(router.urls)),

    # Market Data specific endpoints
    path('market-data/quotes/<uuid:pk>/', MarketDataQuoteView.as_view(), name='market-data-quote-detail'),
    path('market-data/quotes/', MarketDataQuoteView.as_view(), name='market-data-quotes'),
    path('market-data/history/<uuid:pk>/', MarketDataHistoryView.as_view(), name='market-data-history'),
    path('market-data/overview/', MarketDataOverviewView.as_view(), name='market-data-overview'),
    path('market-data/providers/', MarketDataProvidersView.as_view(), name='market-data-providers'),
    path('market-data/health/', MarketDataHealthView.as_view(), name='market-data-health'),
    path('market-data/refresh/<uuid:pk>/', MarketDataRefreshView.as_view(), name='market-data-refresh'),
]
