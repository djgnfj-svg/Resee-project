"""
Email verification service for handling email verification logic.
"""
import hashlib
import logging
import secrets
from datetime import timedelta
from typing import Optional, Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

logger = logging.getLogger(__name__)
User = get_user_model()


class EmailVerificationService:
    """
    Service class for email verification operations.

    Handles:
    - Token generation and hashing
    - Email verification
    - Token expiration checks
    - Rate limiting for resend
    """

    def __init__(self, user: User):
        """
        Initialize EmailVerificationService with a user.

        Args:
            user: User instance to perform operations on
        """
        self.user = user

    def generate_verification_token(self) -> str:
        """
        Generate a unique token for email verification.

        Returns:
            Plain text token to be sent to user via email

        Security:
            - Token is hashed with SHA-256 before storage
            - Only hash is stored in database
            - Plain text token is returned for email sending
        """
        # Generate 32-character URL-safe token
        token = secrets.token_urlsafe(32)

        # Hash token with SHA-256 before storing
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Store hash and timestamp
        self.user.email_verification_token = token_hash
        self.user.email_verification_sent_at = timezone.now()
        self.user.save(update_fields=[
            'email_verification_token',
            'email_verification_sent_at'
        ])

        logger.info(f"Verification token generated for user {self.user.email}")

        # Return plain text token for email
        return token

    def verify_email(self, token: str) -> Tuple[bool, Optional[str]]:
        """
        Verify email with the given token.

        Args:
            token: Plain text token from verification link

        Returns:
            Tuple of (success: bool, error_message: Optional[str])

        Security:
            - Uses constant-time comparison to prevent timing attacks
            - Validates token hash instead of plaintext
            - Checks expiration before comparison
        """
        # Check if token exists
        if not self.user.email_verification_token:
            return False, "No verification token found"

        # Check if already verified
        if self.user.is_email_verified:
            return False, "Email already verified"

        # Check token expiration
        if not self._is_token_valid():
            return False, "Verification token has expired"

        # Hash incoming token for comparison
        token_hash = hashlib.sha256(token.encode()).hexdigest()

        # Constant-time comparison to prevent timing attacks
        if not secrets.compare_digest(
            self.user.email_verification_token,
            token_hash
        ):
            return False, "Invalid verification token"

        # Mark email as verified
        self.user.is_email_verified = True
        self.user.email_verification_token = None
        self.user.email_verification_sent_at = None
        self.user.save(update_fields=[
            'is_email_verified',
            'email_verification_token',
            'email_verification_sent_at'
        ])

        logger.info(f"Email verified for user {self.user.email}")

        return True, None

    def can_resend_verification(self) -> Tuple[bool, Optional[str]]:
        """
        Check if verification email can be resent.

        Rate limit: 5 minutes between resends

        Returns:
            Tuple of (can_resend: bool, error_message: Optional[str])
        """
        # Already verified
        if self.user.is_email_verified:
            return False, "Email already verified"

        # No previous send
        if not self.user.email_verification_sent_at:
            return True, None

        # Check rate limit (5 minutes)
        time_since_sent = timezone.now() - self.user.email_verification_sent_at
        rate_limit = timedelta(minutes=5)

        if time_since_sent <= rate_limit:
            remaining_seconds = (rate_limit - time_since_sent).seconds
            return False, f"Please wait {remaining_seconds} seconds before resending"

        return True, None

    def _is_token_valid(self) -> bool:
        """
        Check if verification token is still valid (not expired).

        Returns:
            True if valid, False if expired
        """
        if not self.user.email_verification_sent_at:
            return False

        expiry_days = getattr(settings, 'EMAIL_VERIFICATION_TIMEOUT_DAYS', 1)
        expiry_time = self.user.email_verification_sent_at + timedelta(
            days=expiry_days
        )

        return timezone.now() <= expiry_time
