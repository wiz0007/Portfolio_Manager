from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.users.api.v1.serializers import (
    LoginSerializer,
    RegisterSerializer,
    ResendVerificationSerializer,
    UserProfileUpdateSerializer,
    UserSerializer,
    VerifyEmailSerializer,
)
from apps.users.services.auth_service import AuthService
from apps.users.services.email_verification import EmailVerificationService
from apps.users.services.user_service import UserService


class CSRFTokenView(APIView):
    """
    Endpoint to initialize and return the CSRF cookie/token for state-changing API calls.
    """

    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    @extend_schema(
        summary="Initialize CSRF Token",
        description="Sets the CSRF cookie and returns the token for SPA state-changing requests.",
        responses={200: OpenApiResponse(description="CSRF cookie initialized")},
        tags=["Authentication"],
    )
    def get(self, request):
        token = get_token(request)
        return Response(
            {"detail": "CSRF cookie set", "csrfToken": token},
            status=status.HTTP_200_OK,
        )


class RegisterView(APIView):
    """
    Register a new user account with validated email, full name, and password.
    """

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    @extend_schema(
        summary="Register New User",
        description="Creates a new account, sends a verification email, and returns the created user profile.",
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(response=UserSerializer, description="User successfully registered"),
            400: OpenApiResponse(description="Validation error"),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Send verification email asynchronously / via email backend
        EmailVerificationService.send_verification_email(user)

        # Establish session upon registration
        AuthService.login_user(request, user)

        return Response(
            {
                "message": "User registered successfully.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    Authenticate user using email and password, establishing an HTTP-only session.
    """

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    @extend_schema(
        summary="User Login",
        description="Verifies credentials and establishes an authenticated session cookie.",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(response=UserSerializer, description="Login successful"),
            400: OpenApiResponse(description="Invalid credentials or inactive account"),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        AuthService.login_user(request, user)

        return Response(
            {
                "message": "Login successful.",
                "user": UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    Invalidate the current session and clear authentication cookies.
    """

    permission_classes = [AllowAny]

    @extend_schema(
        summary="User Logout",
        description="Terminates the user session and flushes session cookies.",
        request=None,
        responses={200: OpenApiResponse(description="Successfully logged out")},
        tags=["Authentication"],
    )
    def post(self, request):
        AuthService.logout_user(request)
        return Response(
            {"message": "Logged out successfully."},
            status=status.HTTP_200_OK,
        )


class VerifyEmailView(APIView):
    """
    Validates a cryptographic email verification token and marks the account's email as verified.
    """

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    @extend_schema(
        summary="Verify Email Address",
        description="Validates a secure time-limited token and verifies the user's email address.",
        request=VerifyEmailSerializer,
        responses={
            200: OpenApiResponse(description="Email verified successfully or already verified"),
            400: OpenApiResponse(description="Invalid or expired token"),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']

        success, code, _user = EmailVerificationService.verify_token(token)
        if success:
            if code == 'already_verified':
                return Response(
                    {"message": "Email is already verified.", "status": "already_verified"},
                    status=status.HTTP_200_OK,
                )
            return Response(
                {"message": "Email address verified successfully.", "status": "verified"},
                status=status.HTTP_200_OK,
            )

        if code == 'expired':
            return Response(
                {"detail": "Verification link has expired. Please request a new one.", "code": "expired"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {"detail": "Invalid or tampered verification link.", "code": "invalid"},
            status=status.HTTP_400_BAD_REQUEST,
        )


class ResendVerificationView(APIView):
    """
    Requests a fresh verification email link for an unverified account.
    """

    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    @extend_schema(
        summary="Resend Verification Email",
        description="Resends a time-limited verification email link with rate-limiting defense.",
        request=ResendVerificationSerializer,
        responses={
            200: OpenApiResponse(description="Generic confirmation response"),
            429: OpenApiResponse(description="Too many requests"),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data.get('email')

        if not email and request.user and request.user.is_authenticated:
            email = request.user.email

        if not email:
            return Response(
                {"detail": "Email address is required to resend verification."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        allowed, code = EmailVerificationService.resend_verification_email(email)
        if not allowed and code == 'rate_limited':
            return Response(
                {"detail": "Too many verification requests. Please try again later.", "code": "rate_limited"},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        return Response(
            {"message": "If an unverified account exists with this email, a verification link has been sent."},
            status=status.HTTP_200_OK,
        )


class CurrentUserView(APIView):
    """
    Retrieve or update current authenticated user profile.
    """

    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Current User Profile",
        description="Returns the profile information of the currently authenticated user.",
        responses={
            200: UserSerializer,
            401: OpenApiResponse(description="Unauthenticated"),
        },
        tags=["Authentication", "User Profile"],
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Update User Profile",
        description="Updates the profile information (full_name) for the currently authenticated user.",
        request=UserProfileUpdateSerializer,
        responses={
            200: UserSerializer,
            400: OpenApiResponse(description="Validation error"),
            401: OpenApiResponse(description="Unauthenticated"),
        },
        tags=["User Profile"],
    )
    def patch(self, request):
        serializer = UserProfileUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = UserService.update_profile(
            request.user,
            full_name=serializer.validated_data['full_name'],
        )
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
