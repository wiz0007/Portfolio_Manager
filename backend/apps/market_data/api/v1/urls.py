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
    MarketDataSeriesListView,
    MarketDataSeriesVersionView,
)
from apps.market_data.api.v1.views.operations import (
    BulkPriceResolverView,
    DatabaseHealthView,
    HistoricalBackfillTriggerView,
    HistoricalCoverageReportView,
    InstrumentCoverageViewSet,
    InstrumentRequestViewSet,
    MarketDataWorklistViewSet,
    PriceImportCommitView,
    PriceImportPreviewView,
    PriceObservationViewSet,
    PriceResolverView,
)

router = DefaultRouter()
router.register(r'instruments', InstrumentViewSet, basename='instrument')
router.register(r'market-data/requests', InstrumentRequestViewSet, basename='market-data-request')
router.register(r'market-data/coverage', InstrumentCoverageViewSet, basename='market-data-coverage')
router.register(r'market-data/worklists', MarketDataWorklistViewSet, basename='market-data-worklist')
router.register(r'market-data/observations', PriceObservationViewSet, basename='market-data-observation')

urlpatterns = [
    # Router endpoints
    path('', include(router.urls)),

    # Market Data specific endpoints
    path('market-data/quotes/<uuid:pk>/', MarketDataQuoteView.as_view(), name='market-data-quote-detail'),
    path('market-data/quotes/', MarketDataQuoteView.as_view(), name='market-data-quotes'),
    path('market-data/history/<uuid:pk>/', MarketDataHistoryView.as_view(), name='market-data-history'),
    path('market-data/series/', MarketDataSeriesListView.as_view(), name='market-data-series-list'),
    path('market-data/series/<uuid:pk>/version/', MarketDataSeriesVersionView.as_view(), name='market-data-series-version'),
    path('market-data/overview/', MarketDataOverviewView.as_view(), name='market-data-overview'),
    path('market-data/providers/', MarketDataProvidersView.as_view(), name='market-data-providers'),
    path('market-data/health/', MarketDataHealthView.as_view(), name='market-data-health'),
    path('market-data/refresh/<uuid:pk>/', MarketDataRefreshView.as_view(), name='market-data-refresh'),

    # Manual Market-Data Operations & Import
    path('market-data/import/preview/', PriceImportPreviewView.as_view(), name='market-data-import-preview'),
    path('market-data/import/commit/', PriceImportCommitView.as_view(), name='market-data-import-commit'),
    path('market-data/resolve/<uuid:instrument_id>/', PriceResolverView.as_view(), name='market-data-resolve'),
    path('market-data/prices/bulk-resolve/', BulkPriceResolverView.as_view(), name='market-data-bulk-resolve'),
    path('market-data/operations/database-health/', DatabaseHealthView.as_view(), name='market-data-database-health'),
    path('market-data/operations/history-coverage/', HistoricalCoverageReportView.as_view(), name='market-data-history-coverage'),
    path('market-data/operations/history-backfill/', HistoricalBackfillTriggerView.as_view(), name='market-data-history-backfill'),
]
