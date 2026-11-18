from django.urls import path

from apps.dashboard.api.v1.views.dashboard import (
    AssetAllocationView,
    DashboardOverviewView,
    DataQualityView,
    HoldingsOverviewView,
    RecentActivityView,
    WatchlistPreviewView,
)

app_name = 'dashboard_api_v1'

urlpatterns = [
    path('overview/', DashboardOverviewView.as_view(), name='dashboard-overview'),
    path('allocation/', AssetAllocationView.as_view(), name='dashboard-allocation'),
    path('holdings/', HoldingsOverviewView.as_view(), name='dashboard-holdings'),
    path('recent-activity/', RecentActivityView.as_view(), name='dashboard-recent-activity'),
    path('data-quality/', DataQualityView.as_view(), name='dashboard-data-quality'),
    path('watchlist-preview/', WatchlistPreviewView.as_view(), name='dashboard-watchlist-preview'),
]
