from django.urls import path

from apps.dashboard.api.v1.views.dashboard import DashboardOverviewView

app_name = 'dashboard_api_v1'

urlpatterns = [
    path('overview/', DashboardOverviewView.as_view(), name='dashboard-overview'),
]
