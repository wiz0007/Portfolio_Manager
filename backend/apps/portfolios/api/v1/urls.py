from django.urls import path

from apps.portfolios.api.v1.views import PortfolioDetailView, PortfolioListCreateView

app_name = 'portfolios_api_v1'

urlpatterns = [
    path('', PortfolioListCreateView.as_view(), name='portfolio-list-create'),
    path('<uuid:id>/', PortfolioDetailView.as_view(), name='portfolio-detail'),
]
