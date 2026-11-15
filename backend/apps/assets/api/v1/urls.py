from django.urls import path

from apps.assets.api.v1.views import InvestmentDetailView, InvestmentListCreateView

app_name = 'assets_api_v1'

urlpatterns = [
    path('investments/', InvestmentListCreateView.as_view(), name='investment-list-create'),
    path('investments/<uuid:id>/', InvestmentDetailView.as_view(), name='investment-detail'),
    path('portfolios/<uuid:portfolio_id>/investments/', InvestmentListCreateView.as_view(), name='portfolio-investment-list-create'),
    path('portfolios/<uuid:portfolio_id>/investments/<uuid:id>/', InvestmentDetailView.as_view(), name='portfolio-investment-detail'),
]
