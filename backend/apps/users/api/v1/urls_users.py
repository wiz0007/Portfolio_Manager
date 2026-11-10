from django.urls import path

from apps.users.api.v1.views import CurrentUserView

app_name = 'users_profile_api_v1'

urlpatterns = [
    path('me/', CurrentUserView.as_view(), name='user-me'),
]
