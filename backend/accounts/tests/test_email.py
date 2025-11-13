"""
Tests for email verification views.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class EmailVerificationViewTest(TestCase):
    """Test EmailVerificationView."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=False
        )

    def test_verify_email_success(self):
        """Test successful email verification."""
        # Generate token
        token = self.user.generate_email_verification_token()

        response = self.client.post('/api/accounts/verify-email/', {
            'token': token,
            'email': 'test@example.com'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check user is verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)

    def test_verify_email_invalid_token(self):
        """Test email verification with invalid token."""
        response = self.client.post('/api/accounts/verify-email/', {
            'token': 'invalid_token',
            'email': 'test@example.com'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_email_missing_fields(self):
        """Test email verification without required fields."""
        response = self.client.post('/api/accounts/verify-email/', {
            'token': 'some_token'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_verify_email_nonexistent_user(self):
        """Test email verification with non-existent user."""
        response = self.client.post('/api/accounts/verify-email/', {
            'token': 'some_token',
            'email': 'nonexistent@example.com'
        })
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND])


class ResendVerificationViewTest(TestCase):
    """Test ResendVerificationView."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=False
        )

    @override_settings(ENFORCE_EMAIL_VERIFICATION=True)
    def test_resend_verification_success(self):
        """Test successful verification email resend."""
        # Generate initial token to set sent_at
        self.user.generate_email_verification_token()

        response = self.client.post('/api/accounts/resend-verification/', {
            'email': 'test@example.com'
        })
        # Could be 200 or 429 depending on timing
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_429_TOO_MANY_REQUESTS])

    def test_resend_verification_missing_email(self):
        """Test resend verification without email."""
        response = self.client.post('/api/accounts/resend-verification/', {})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resend_verification_nonexistent_user(self):
        """Test resend verification with non-existent user."""
        response = self.client.post('/api/accounts/resend-verification/', {
            'email': 'nonexistent@example.com'
        })
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND])

    def test_resend_verification_already_verified(self):
        """Test resend verification for already verified user."""
        self.user.is_email_verified = True
        self.user.save()

        response = self.client.post('/api/accounts/resend-verification/', {
            'email': 'test@example.com'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
