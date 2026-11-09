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
    UserSerializer,
)
from apps.users.services.auth_service import AuthService


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
        tags=["Authentication"]
    )
    def get(self, request):
        token = get_token(request)
        return Response(
            {"detail": "CSRF cookie set", "csrfToken": token},
            status=status.HTTP_200_OK
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
        description="Creates a new account and returns the created user profile.",
        request=RegisterSerializer,
        responses={
            201: OpenApiResponse(response=UserSerializer, description="User successfully registered"),
            400: OpenApiResponse(description="Validation error"),
        },
        tags=["Authentication"]
    )
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

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
        tags=["Authentication"]
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
        tags=["Authentication"]
    )
    def post(self, request):
        AuthService.logout_user(request)
        return Response(
            {"message": "Logged out successfully."},
            status=status.HTTP_200_OK,
        )


class CurrentUserView(APIView):
    """
    Retrieve current authenticated user profile.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary="Current User Profile",
        description="Returns the profile information of the currently authenticated user.",
        responses={
            200: UserSerializer,
            401: OpenApiResponse(description="Unauthenticated"),
        },
        tags=["Authentication"]
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
