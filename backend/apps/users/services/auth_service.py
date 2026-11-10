from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.http import HttpRequest

from apps.users.models import User


class AuthService:
    """Service handling user authentication and session management."""

    @staticmethod
    def register_user(full_name: str, email: str, password: str) -> User:
        """Create and return a new user record."""
        return User.objects.create_user(
            email=email,
            password=password,
            full_name=full_name,
        )

    @staticmethod
    def login_user(request: HttpRequest, user: User) -> None:
        """
        Log user in and regenerate session key to guard against session fixation.
        """
        django_login(request, user)
        if hasattr(request, 'session'):
            request.session.cycle_key()

    @staticmethod
    def logout_user(request: HttpRequest) -> None:
        """Flush the user's session and delete the session cookie."""
        django_logout(request)
