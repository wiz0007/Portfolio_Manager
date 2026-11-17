from django.urls import path

from apps.valuation.api.v1.views import (
    InvestmentCalculateValuationView,
    InvestmentPerformanceView,
    InvestmentProjectionCalculateView,
    InvestmentValuationDetailView,
    InvestmentValuationListCreateView,
)

app_name = 'valuation_api_v1'

urlpatterns = [
    path(
        'investments/<uuid:investment_id>/valuations/calculate/',
        InvestmentCalculateValuationView.as_view(),
        name='investment-valuation-calculate',
    ),
    path(
        'investments/<uuid:investment_id>/valuations/',
        InvestmentValuationListCreateView.as_view(),
        name='investment-valuation-list-create',
    ),
    path(
        'investments/<uuid:investment_id>/valuations/<uuid:id>/',
        InvestmentValuationDetailView.as_view(),
        name='investment-valuation-detail',
    ),
    path(
        'investments/<uuid:investment_id>/performance/',
        InvestmentPerformanceView.as_view(),
        name='investment-performance',
    ),
    path(
        'investments/<uuid:investment_id>/projections/calculate/',
        InvestmentProjectionCalculateView.as_view(),
        name='investment-projection-calculate',
    ),
]
