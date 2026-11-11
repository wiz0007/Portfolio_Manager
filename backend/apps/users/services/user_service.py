from apps.users.models import User


class UserService:
    """Service handling user account modifications and profile operations."""

    @staticmethod
    def update_profile(user: User, *, full_name: str) -> User:
        """
        Update user's full name and persist to database.
        """
        user.full_name = full_name.strip()
        user.save(update_fields=['full_name', 'updated_at'])
        return user
