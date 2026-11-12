from rest_framework import serializers

from apps.portfolios.models import SUPPORTED_CURRENCIES, Portfolio


class PortfolioSerializer(serializers.ModelSerializer):
    """
    Serializer for Portfolio listing, creation, and updates.
    Enforces user isolation and validates currency, name length, and description.
    """

    name = serializers.CharField(
        max_length=100,
        min_length=1,
        trim_whitespace=True,
        required=True,
        error_messages={
            'required': 'Portfolio name is required.',
            'blank': 'Portfolio name cannot be blank.',
            'max_length': 'Portfolio name cannot exceed 100 characters.',
        },
    )
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=1000,
        trim_whitespace=True,
        default='',
        error_messages={
            'max_length': 'Description cannot exceed 1000 characters.',
        },
    )
    base_currency = serializers.CharField(
        required=False,
        default='INR',
        max_length=3,
        error_messages={
            'max_length': 'Currency code cannot exceed 3 characters.',
        },
    )

    class Meta:
        model = Portfolio
        fields = (
            'id',
            'name',
            'description',
            'base_currency',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

    def validate_name(self, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise serializers.ValidationError('Portfolio name cannot be blank.')
        return trimmed

    def validate_base_currency(self, value: str) -> str:
        code = value.strip().upper()
        if code not in SUPPORTED_CURRENCIES:
            raise serializers.ValidationError(
                f"Unsupported currency '{value}'. Supported currencies are: {', '.join(SUPPORTED_CURRENCIES)}."
            )
        return code
