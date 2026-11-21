from django.conf import settings
from rest_framework.permissions import BasePermission


class IsAuthenticatedAndEmailVerified(BasePermission):
    """Require an authenticated, email-verified user when production policy enables it."""

    message = 'Verify your email address before using this feature.'

    def has_permission(self, request, view):
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        if not getattr(settings, 'REQUIRE_VERIFIED_EMAIL_FOR_API', False):
            return True
        return bool(getattr(user, 'is_email_verified', False))
