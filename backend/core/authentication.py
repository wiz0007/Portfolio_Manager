from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import SessionAuthentication


class EnforcedSessionAuthentication(SessionAuthentication):
    """
    SessionAuthentication that provides an authenticate_header.
    This ensures DRF returns HTTP 401 Unauthorized (instead of HTTP 403 Forbidden)
    when an unauthenticated request attempts to access an IsAuthenticated endpoint.
    """

    def authenticate_header(self, request):
        return 'Session realm="api"'


class EnforcedSessionScheme(OpenApiAuthenticationExtension):
    target_class = 'core.authentication.EnforcedSessionAuthentication'
    name = 'cookieAuth'

    def get_security_definition(self, auto_schema):
        return {
            'type': 'apiKey',
            'in': 'cookie',
            'name': 'sessionid',
        }
