import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, Tuple

from django.conf import settings
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.users.models import User

logger = logging.getLogger(__name__)

GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


class GoogleAuthService:
    """Service handling Google OAuth token verification and user provisioning."""

    @classmethod
    def verify_token(cls, token: str) -> Dict[str, Any]:
        """
        Verify the Google token (supports both JWT ID tokens and OAuth2 access tokens).
        """
        if not token or not token.strip():
            raise ValidationError({"credential": "Google token must not be empty."})

        token_str = token.strip()
        if token_str.startswith("ya29") or (not token_str.startswith("ey") and "." not in token_str):
            return cls.verify_access_token(token_str)
        return cls.verify_id_token(token_str)

    @classmethod
    def verify_id_token(cls, id_token: str) -> Dict[str, Any]:
        """
        Verify the Google ID token against Google's tokeninfo API.
        Validates signature/expiry (via Google), issuer, audience, and email verification.
        """
        if not id_token or not id_token.strip():
            raise ValidationError({"credential": "Google ID token must not be empty."})

        query_params = urllib.parse.urlencode({"id_token": id_token.strip()})
        url = f"{GOOGLE_TOKENINFO_URL}?{query_params}"

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "PortfolioManager-Backend"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status != 200:
                    raise ValidationError({"credential": "Invalid or expired Google token."})
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            logger.warning("Google tokeninfo HTTP error: %s", exc)
            raise ValidationError({"credential": "Invalid or expired Google token."}) from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            logger.error("Failed to connect to Google tokeninfo service: %s", exc)
            raise ValidationError({"detail": "Unable to verify token with Google service at this time."}) from exc

        # Verify issuer
        issuer = payload.get("iss", "")
        if issuer not in ("accounts.google.com", "https://accounts.google.com"):
            raise ValidationError({"credential": "Token was not issued by Google."})

        # Verify audience (Client ID)
        configured_client_id = getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", "")
        if configured_client_id:
            audience = payload.get("aud", "")
            if audience != configured_client_id:
                raise ValidationError({"credential": "Token audience does not match configured Google Client ID."})

        # Verify email presence
        email = payload.get("email")
        if not email:
            raise ValidationError({"credential": "Google token does not contain an email address."})

        # Verify email is verified by Google
        email_verified = payload.get("email_verified")
        if email_verified not in (True, "true", "True"):
            raise ValidationError({"detail": "Your Google email address is not verified."})

        return payload

    @classmethod
    def verify_access_token(cls, access_token: str) -> Dict[str, Any]:
        """
        Verify Google OAuth2 access token against Google tokeninfo and userinfo APIs.
        """
        query_params = urllib.parse.urlencode({"access_token": access_token.strip()})
        tokeninfo_url = f"{GOOGLE_TOKENINFO_URL}?{query_params}"

        try:
            req_info = urllib.request.Request(
                tokeninfo_url,
                headers={"User-Agent": "PortfolioManager-Backend"},
                method="GET",
            )
            with urllib.request.urlopen(req_info, timeout=10) as response:
                if response.status != 200:
                    raise ValidationError({"credential": "Invalid or expired Google token."})
                tokeninfo = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            logger.warning("Google access tokeninfo HTTP error: %s", exc)
            raise ValidationError({"credential": "Invalid or expired Google token."}) from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            logger.error("Failed to connect to Google tokeninfo service: %s", exc)
            raise ValidationError({"detail": "Unable to verify token with Google service at this time."}) from exc

        # Verify audience/azp matches configured client ID if set
        configured_client_id = getattr(settings, "GOOGLE_OAUTH_CLIENT_ID", "")
        if configured_client_id:
            token_aud = tokeninfo.get("aud") or tokeninfo.get("azp", "")
            if token_aud != configured_client_id:
                raise ValidationError({"credential": "Token audience does not match configured Google Client ID."})

        # Verify email presence and verification status from tokeninfo
        email = tokeninfo.get("email")
        if not email:
            raise ValidationError({"credential": "Google token does not contain an email address."})

        email_verified = tokeninfo.get("email_verified")
        if email_verified not in (True, "true", "True"):
            raise ValidationError({"detail": "Your Google email address is not verified."})

        # Fetch user profile (name, picture) from userinfo
        try:
            req_user = urllib.request.Request(
                GOOGLE_USERINFO_URL,
                headers={
                    "User-Agent": "PortfolioManager-Backend",
                    "Authorization": f"Bearer {access_token.strip()}",
                },
                method="GET",
            )
            with urllib.request.urlopen(req_user, timeout=10) as user_resp:
                userinfo = json.loads(user_resp.read().decode("utf-8"))
        except Exception as exc:
            logger.warning("Failed to fetch Google userinfo, falling back to tokeninfo: %s", exc)
            userinfo = {}

        return {
            "email": email,
            "name": userinfo.get("name") or tokeninfo.get("name", ""),
            "sub": userinfo.get("sub") or tokeninfo.get("sub", ""),
            "email_verified": True,
        }

    @classmethod
    def authenticate_or_register_user(cls, google_payload: Dict[str, Any]) -> Tuple[User, bool]:
        """
        Find existing user or create a new user from Google identity payload.
        Ensures email_verified_at is set for Google-verified identities.
        Returns a tuple of (user, created).
        """
        raw_email = google_payload.get("email", "").strip()
        email = User.objects.normalize_email(raw_email).lower()

        full_name = google_payload.get("name", "").strip()
        if not full_name:
            given = google_payload.get("given_name", "").strip()
            family = google_payload.get("family_name", "").strip()
            full_name = f"{given} {family}".strip() or email.split("@")[0]

        now = timezone.now()

        try:
            user = User.objects.get(email__iexact=email)
            created = False

            if not user.is_active:
                raise ValidationError({"detail": "This account is inactive."})

            # Since Google confirms the email is verified, set email_verified_at if not set
            if user.email_verified_at is None:
                user.email_verified_at = now
                user.save(update_fields=["email_verified_at", "updated_at"])

        except User.DoesNotExist:
            user = User.objects.create_user(
                email=email,
                full_name=full_name,
                password=None,
                is_active=True,
                email_verified_at=now,
            )
            created = True

        return user, created
