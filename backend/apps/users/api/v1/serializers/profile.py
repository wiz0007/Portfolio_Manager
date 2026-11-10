from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserProfileUpdateSerializer(serializers.Serializer):
    """
    Serializer for updating the authenticated user's profile.
    Only allows updating non-sensitive personal profile information (full_name).
    Rejects or ignores sensitive fields like email, is_staff, is_active, password.
    """

    full_name = serializers.CharField(
        max_length=255,
        min_length=2,
        required=True,
        trim_whitespace=True,
        error_messages={
            'required': 'Full name is required.',
            'blank': 'Full name cannot be blank.',
            'min_length': 'Full name must be at least 2 characters.',
            'max_length': 'Full name cannot exceed 255 characters.',
        }
    )

    def validate_full_name(self, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise serializers.ValidationError('Full name cannot be blank.')
        if len(trimmed) < 2:
            raise serializers.ValidationError('Full name must be at least 2 characters.')
        return trimmed
