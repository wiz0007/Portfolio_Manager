import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()

@pytest.mark.django_db
class TestUserModel:
    """Unit tests for the custom User model and manager."""

    def test_create_user_successful(self):
        user = User.objects.create_user(
            email='test@example.com',
            password='StrongPassword123!',
            full_name='Test User'
        )
        assert user.email == 'test@example.com'
        assert user.full_name == 'Test User'
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
        assert user.check_password('StrongPassword123!')
        assert not user.check_password('WrongPassword')
        assert str(user) == 'test@example.com'

    def test_create_user_normalizes_email(self):
        user = User.objects.create_user(
            email='User.Name+Test@EXAMPLE.COM',
            password='StrongPassword123!',
            full_name='Case User'
        )
        assert user.email == 'User.Name+Test@example.com'

    def test_create_user_without_email_raises_error(self):
        with pytest.raises(ValueError, match="The Email field must be set"):
            User.objects.create_user(
                email='',
                password='StrongPassword123!',
                full_name='No Email'
            )

    def test_duplicate_email_raises_integrity_error(self):
        User.objects.create_user(
            email='unique@example.com',
            password='Password123!',
            full_name='User One'
        )
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                email='unique@example.com',
                password='Password456!',
                full_name='User Two'
            )

    def test_create_superuser(self):
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='AdminPassword123!',
            full_name='Admin User'
        )
        assert admin.is_staff is True
        assert admin.is_superuser is True
        assert admin.is_active is True
