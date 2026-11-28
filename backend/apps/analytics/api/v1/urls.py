from django.urls import path

from apps.analytics.api.v1.views import (
    BenchmarkListView,
    InvestmentPerformanceView,
    PortfolioAllocationView,
    PortfolioBenchmarkComparisonView,
    PortfolioPerformanceView,
)

app_name = 'analytics_api_v1'

urlpatterns = [
    path('investments/<uuid:pk>/performance/', InvestmentPerformanceView.as_view(), name='investment-performance'),
    path('portfolios/<uuid:pk>/performance/', PortfolioPerformanceView.as_view(), name='portfolio-performance'),
    path('portfolios/<uuid:pk>/allocation/', PortfolioAllocationView.as_view(), name='portfolio-allocation'),
    path('portfolios/<uuid:pk>/benchmark-comparison/', PortfolioBenchmarkComparisonView.as_view(), name='portfolio-benchmark-comparison'),
    path('benchmarks/', BenchmarkListView.as_view(), name='benchmark-list'),
]
