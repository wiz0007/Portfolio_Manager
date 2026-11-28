from django.urls import path

from apps.ai_insights.api.v1.views import AIExplainView, AIStatusView

app_name = 'ai_insights_v1'

urlpatterns = [
    path('explain/', AIExplainView.as_view(), name='ai-explain'),
    path('status/', AIStatusView.as_view(), name='ai-status'),
]
