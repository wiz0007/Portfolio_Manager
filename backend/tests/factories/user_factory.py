import uuid

from django.utils import timezone

from apps.users.models import User


def create_test_user(
    email: str | None = None,
    password: str = "ValidPassword123!",
    full_name: str = "Test Investor",
    is_active: bool = True,
    is_verified: bool = True,
) -> User:
    unique_email = email or f"investor_{uuid.uuid4().hex[:8]}@example.com"
    user = User.objects.create_user(
        email=unique_email,
        password=password,
        full_name=full_name,
        is_active=is_active,
    )
    if is_verified:
        user.email_verified_at = timezone.now()
        user.save(update_fields=['email_verified_at'])
    return user
