from django.urls import path

from apps.users.api.v1.views import (
    CSRFTokenView,
    CurrentUserView,
    GoogleAuthView,
    LoginView,
    LogoutView,
    RegisterView,
    ResendVerificationView,
    VerifyEmailView,
)

app_name = 'users_api_v1'

urlpatterns = [
    path('csrf/', CSRFTokenView.as_view(), name='auth-csrf'),
    path('register/', RegisterView.as_view(), name='auth-register'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('google/', GoogleAuthView.as_view(), name='auth-google'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('me/', CurrentUserView.as_view(), name='auth-me'),
    path('verify-email/', VerifyEmailView.as_view(), name='auth-verify-email'),
    path('resend-verification/', ResendVerificationView.as_view(), name='auth-resend-verification'),
]
