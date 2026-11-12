import logging

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.core.signing import BadSignature, SignatureExpired, TimestampSigner
from django.utils import timezone

from apps.users.models import User

logger = logging.getLogger(__name__)

SIGNER_SALT = "email-verification"
RATE_LIMIT_MAX_REQUESTS = 3
RATE_LIMIT_WINDOW_SECONDS = 3600  # 1 hour


class EmailVerificationService:
    """
    Cryptographically secure, time-limited email verification token management and delivery.
    """

    @classmethod
    def get_signer(cls) -> TimestampSigner:
        return TimestampSigner(salt=SIGNER_SALT)

    @classmethod
    def generate_token(cls, user: User) -> str:
        """
        Generates a signed, time-stamped token bound to the user's UUID and email.
        If the user changes their email in the future, previously issued tokens are automatically invalidated.
        """
        signer = cls.get_signer()
        payload = f"{user.id}:{user.email.lower()}"
        return signer.sign(payload)

    @classmethod
    def verify_token(cls, token: str) -> tuple[bool, str, User | None]:
        """
        Validates the verification token signature, expiration, and user binding.
        Returns:
            (success: bool, status_code: str, user: User | None)
            status_code is one of:
            - 'verified': successfully verified email for the first time
            - 'already_verified': user was already verified (safe idempotent outcome)
            - 'expired': token valid signature but expired
            - 'invalid': tampered, malformed, or user not found
        """
        if not token or not isinstance(token, str):
            return False, "invalid", None

        signer = cls.get_signer()
        timeout = getattr(settings, "EMAIL_VERIFICATION_TIMEOUT", 1800)

        try:
            payload = signer.unsign(token, max_age=timeout)
        except SignatureExpired:
            return False, "expired", None
        except BadSignature:
            return False, "invalid", None
        except Exception:
            return False, "invalid", None

        parts = payload.split(":", 1)
        if len(parts) != 2:
            return False, "invalid", None

        user_id_str, email_str = parts

        try:
            user = User.objects.get(id=user_id_str)
        except (User.DoesNotExist, ValueError):
            return False, "invalid", None

        # Invalidate if user's current email doesn't match the token's email
        if user.email.lower() != email_str.lower():
            return False, "invalid", None

        if user.email_verified_at is not None:
            return True, "already_verified", user

        user.email_verified_at = timezone.now()
        user.save(update_fields=["email_verified_at", "updated_at"])
        return True, "verified", user

    @classmethod
    def send_verification_email(cls, user: User) -> bool:
        """
        Sends verification email containing the unique secure link to the user.
        """
        token = cls.generate_token(user)
        base_url = getattr(settings, "FRONTEND_BASE_URL", "http://localhost:5173").rstrip("/")
        verification_link = f"{base_url}/verify-email?token={token}"
        timeout_minutes = getattr(settings, "EMAIL_VERIFICATION_TIMEOUT", 1800) // 60

        subject = "Verify your Portfolio Manager email address"
        message = (
            f"Hello {user.full_name},\n\n"
            f"Thank you for registering with Portfolio Manager.\n\n"
            f"Please verify your email address by clicking the link below:\n"
            f"{verification_link}\n\n"
            f"This link will expire in {timeout_minutes} minutes.\n\n"
            f"If you did not create an account, please disregard this email."
        )

        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            return True
        except Exception:
            logger.exception("Failed to send verification email to %s", user.email)
            return False

    @classmethod
    def check_resend_rate_limit(cls, user_id: str) -> bool:
        """
        Enforces a maximum of 3 resend attempts per user per hour.
        Returns True if allowed, False if rate limited.
        """
        cache_key = f"email_verify_resend_{user_id}"
        attempts = cache.get(cache_key, 0)
        if attempts >= RATE_LIMIT_MAX_REQUESTS:
            return False
        cache.set(cache_key, attempts + 1, timeout=RATE_LIMIT_WINDOW_SECONDS)
        return True

    @classmethod
    def resend_verification_email(cls, email: str) -> tuple[bool, str]:
        """
        Handles resending a verification email.
        Applies rate limiting and returns a safe response without revealing whether the email exists.
        """
        normalized_email = email.strip().lower()
        try:
            user = User.objects.get(email__iexact=normalized_email)
        except User.DoesNotExist:
            # Safe generic response to prevent account enumeration
            return True, "sent"

        if user.email_verified_at is not None:
            # Already verified
            return True, "already_verified"

        if not cls.check_resend_rate_limit(str(user.id)):
            return False, "rate_limited"

        sent = cls.send_verification_email(user)
        return sent, "sent" if sent else "send_failed"
