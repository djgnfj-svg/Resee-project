"""
Authentication service layer for handling auth-related business logic.
"""
import logging
from typing import Optional, Tuple

from django.contrib.auth import get_user_model
from django.db import transaction

logger = logging.getLogger(__name__)
User = get_user_model()


class AuthService:
    """
    Service class for authentication-related operations.

    Handles:
    - Password changes
    - JWT token blacklisting
    - Authentication validation
    """

    def __init__(self, user: User):
        """
        Initialize AuthService with a user.

        Args:
            user: User instance to perform operations on
        """
        self.user = user

    @transaction.atomic
    def change_password(
        self,
        current_password: str,
        new_password: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Change user password and blacklist all existing JWT tokens.

        This is a critical security operation that:
        1. Validates current password
        2. Changes to new password
        3. Blacklists all existing JWT tokens

        Args:
            current_password: User's current password
            new_password: New password to set

        Returns:
            Tuple of (success: bool, error_message: Optional[str])

        Security:
            - All JWT tokens are blacklisted to prevent unauthorized access
            - Operation is atomic (all-or-nothing)
        """
        # Validate current password
        if not self.user.check_password(current_password):
            return False, "Current password is incorrect"

        try:
            # Change password
            self.user.set_password(new_password)
            self.user.save()

            # Blacklist all existing tokens
            tokens_blacklisted = self._blacklist_all_tokens()

            logger.info(
                f"Password changed and {tokens_blacklisted} tokens "
                f"blacklisted for user {self.user.email}"
            )

            return True, None

        except Exception as e:
            logger.error(
                f"Password change failed for user {self.user.email}: {str(e)}",
                exc_info=True
            )
            return False, "Password change failed"

    def _blacklist_all_tokens(self) -> int:
        """
        Blacklist all outstanding JWT tokens for the user.

        Returns:
            Number of tokens blacklisted

        Security:
            This ensures that after password change, all existing
            tokens become invalid immediately.
        """
        try:
            from rest_framework_simplejwt.token_blacklist.models import (
                BlacklistedToken,
                OutstandingToken
            )

            # Get all outstanding tokens for this user
            outstanding_tokens = OutstandingToken.objects.filter(
                user=self.user
            )

            count = 0
            for token in outstanding_tokens:
                # Add to blacklist if not already blacklisted
                _, created = BlacklistedToken.objects.get_or_create(token=token)
                if created:
                    count += 1

            return count

        except ImportError:
            # token_blacklist not installed
            logger.warning(
                "token_blacklist not available. "
                "Old tokens will remain valid until expiration."
            )
            return 0

    @staticmethod
    def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
        """
        Validate password strength.

        Args:
            password: Password to validate

        Returns:
            Tuple of (is_valid: bool, error_message: Optional[str])
        """
        from ..constants import MIN_PASSWORD_LENGTH, MAX_PASSWORD_LENGTH

        if len(password) < MIN_PASSWORD_LENGTH:
            return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long"

        if len(password) > MAX_PASSWORD_LENGTH:
            return False, f"Password must not exceed {MAX_PASSWORD_LENGTH} characters"

        # Add more validation rules as needed
        # - Must contain uppercase
        # - Must contain lowercase
        # - Must contain digit
        # - Must contain special character

        return True, None


class JWTTokenService:
    """
    Service class for JWT token operations.
    """

    @staticmethod
    def blacklist_token(token_string: str) -> bool:
        """
        Blacklist a specific JWT token.

        Args:
            token_string: JWT token string to blacklist

        Returns:
            True if successfully blacklisted, False otherwise
        """
        try:
            from rest_framework_simplejwt.token_blacklist.models import (
                BlacklistedToken,
                OutstandingToken
            )
            from rest_framework_simplejwt.tokens import RefreshToken

            # Decode token to get jti
            token = RefreshToken(token_string)
            jti = token['jti']

            # Find outstanding token
            outstanding_token = OutstandingToken.objects.filter(jti=jti).first()

            if outstanding_token:
                BlacklistedToken.objects.get_or_create(token=outstanding_token)
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to blacklist token: {str(e)}")
            return False

    @staticmethod
    def is_token_blacklisted(token_string: str) -> bool:
        """
        Check if a JWT token is blacklisted.

        Args:
            token_string: JWT token string to check

        Returns:
            True if blacklisted, False otherwise
        """
        try:
            from rest_framework_simplejwt.token_blacklist.models import (
                BlacklistedToken,
                OutstandingToken
            )
            from rest_framework_simplejwt.tokens import RefreshToken

            # Decode token to get jti
            token = RefreshToken(token_string)
            jti = token['jti']

            # Check if blacklisted
            outstanding_token = OutstandingToken.objects.filter(jti=jti).first()

            if outstanding_token:
                return BlacklistedToken.objects.filter(
                    token=outstanding_token
                ).exists()

            return False

        except Exception as e:
            logger.error(f"Failed to check token blacklist status: {str(e)}")
            return False
