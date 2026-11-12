from rest_framework import serializers


class VerifyEmailSerializer(serializers.Serializer):
    """Serializer validating email verification token submission."""

    token = serializers.CharField(
        required=True,
        allow_blank=False,
        error_messages={
            'required': 'Verification token is required.',
            'blank': 'Verification token cannot be blank.',
        },
    )


class ResendVerificationSerializer(serializers.Serializer):
    """Serializer validating resend email verification request."""

    email = serializers.EmailField(
        required=False,
        allow_blank=True,
        error_messages={
            'invalid': 'Enter a valid email address.',
        },
    )
