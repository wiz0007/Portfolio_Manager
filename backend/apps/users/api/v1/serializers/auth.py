from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    """Serializer for public user profile representation."""

    is_email_verified = serializers.BooleanField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'full_name', 'email', 'date_joined', 'is_active', 'is_email_verified', 'email_verified_at')
        read_only_fields = ('id', 'email', 'date_joined', 'is_active', 'is_email_verified', 'email_verified_at')


class RegisterSerializer(serializers.Serializer):
    """Serializer for user registration with strict validation."""

    full_name = serializers.CharField(
        max_length=255,
        min_length=2,
        required=True,
        trim_whitespace=True,
        error_messages={
            'required': 'Full name is required.',
            'blank': 'Full name cannot be blank.',
            'min_length': 'Full name must be at least 2 characters.',
        }
    )
    email = serializers.EmailField(
        required=True,
        error_messages={
            'required': 'Email address is required.',
            'invalid': 'Enter a valid email address.',
        }
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        error_messages={
            'required': 'Password is required.',
            'blank': 'Password cannot be blank.',
        }
    )
    password_confirmation = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        error_messages={
            'required': 'Password confirmation is required.',
            'blank': 'Password confirmation cannot be blank.',
        }
    )

    def validate_email(self, value):
        normalized_email = User.objects.normalize_email(value).lower()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError('A user with this email address already exists.')
        return normalized_email

    def validate(self, attrs):
        password = attrs.get('password')
        password_confirmation = attrs.get('password_confirmation')

        if password != password_confirmation:
            raise serializers.ValidationError({
                'password_confirmation': 'Passwords do not match.'
            })

        # Validate password strength using Django's password validators
        try:
            validate_password(password)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({
                'password': list(exc.messages)
            })

        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirmation')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            full_name=validated_data['full_name'],
        )
        return user


class LoginSerializer(serializers.Serializer):
    """Serializer for user login verification."""

    email = serializers.EmailField(
        required=True,
        error_messages={
            'required': 'Email is required.',
            'invalid': 'Enter a valid email address.',
        }
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'},
        error_messages={
            'required': 'Password is required.',
            'blank': 'Password cannot be blank.',
        }
    )

    def validate(self, attrs):
        email = User.objects.normalize_email(attrs.get('email')).lower()
        password = attrs.get('password')

        # Generic authentication failure message as per FR-02 security requirements
        auth_error_message = 'Invalid email or password.'

        try:
            user_obj = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            raise serializers.ValidationError({'detail': auth_error_message})

        if not user_obj.check_password(password):
            raise serializers.ValidationError({'detail': auth_error_message})

        if not user_obj.is_active:
            raise serializers.ValidationError({'detail': 'This account is inactive.'})

        attrs['user'] = user_obj
        return attrs


class GoogleAuthSerializer(serializers.Serializer):
    """Serializer for Google OAuth credential authentication."""

    credential = serializers.CharField(
        required=False,
        allow_blank=False,
        trim_whitespace=True,
        help_text="Google OAuth ID token or access token.",
    )
    id_token = serializers.CharField(
        required=False,
        allow_blank=False,
        trim_whitespace=True,
        help_text="Alias for Google ID token.",
    )
    access_token = serializers.CharField(
        required=False,
        allow_blank=False,
        trim_whitespace=True,
        help_text="Google OAuth2 access token.",
    )

    def validate(self, attrs):
        token = attrs.get('credential') or attrs.get('id_token') or attrs.get('access_token')
        if not token:
            raise serializers.ValidationError({
                'credential': 'Google credential, id_token, or access_token is required.'
            })
        attrs['token'] = token
        return attrs

