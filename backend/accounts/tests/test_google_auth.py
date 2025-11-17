"""
Tests for Google OAuth authentication.
"""
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from accounts.auth.google_auth import (
    GoogleAuthSerializer, GoogleAuthService, GoogleOAuthError,
)

User = get_user_model()


class GoogleAuthServiceTest(TestCase):
    """Test GoogleAuthService."""

    @override_settings(SOCIALACCOUNT_PROVIDERS={
        'google': {
            'APP': {
                'client_id': 'test-client-id'
            }
        }
    })
    @patch('accounts.auth.google_auth.id_token.verify_oauth2_token')
    def test_verify_google_token_success(self, mock_verify):
        """Test successful Google token verification."""
        mock_verify.return_value = {
            'iss': 'accounts.google.com',
            'email': 'test@example.com',
            'given_name': 'Test',
            'family_name': 'User'
        }

        result = GoogleAuthService.verify_google_token('valid-token')

        self.assertEqual(result['email'], 'test@example.com')
        self.assertEqual(result['iss'], 'accounts.google.com')

    @override_settings(SOCIALACCOUNT_PROVIDERS={
        'google': {
            'APP': {
                'client_id': ''
            }
        }
    })
    def test_verify_google_token_no_client_id(self):
        """Test token verification without client ID."""
        with self.assertRaises(GoogleOAuthError) as context:
            GoogleAuthService.verify_google_token('token')

        self.assertIn('client ID', str(context.exception))

    @override_settings(SOCIALACCOUNT_PROVIDERS={
        'google': {
            'APP': {
                'client_id': 'test-client-id'
            }
        }
    })
    @patch('accounts.auth.google_auth.id_token.verify_oauth2_token')
    def test_verify_google_token_invalid_issuer(self, mock_verify):
        """Test token verification with invalid issuer."""
        mock_verify.return_value = {
            'iss': 'invalid-issuer.com',
            'email': 'test@example.com'
        }

        with self.assertRaises(GoogleOAuthError) as context:
            GoogleAuthService.verify_google_token('token')

        self.assertIn('발급자', str(context.exception))

    @override_settings(SOCIALACCOUNT_PROVIDERS={
        'google': {
            'APP': {
                'client_id': 'test-client-id'
            }
        }
    })
    @patch('accounts.auth.google_auth.id_token.verify_oauth2_token')
    def test_verify_google_token_value_error(self, mock_verify):
        """Test token verification with ValueError."""
        mock_verify.side_effect = ValueError('Invalid token')

        with self.assertRaises(GoogleOAuthError) as context:
            GoogleAuthService.verify_google_token('invalid-token')

        self.assertIn('검증 실패', str(context.exception))

    def test_get_or_create_user_existing(self):
        """Test getting existing user."""
        user = User.objects.create_user(
            email='existing@example.com',
            password='pass123',
            is_email_verified=False
        )

        google_info = {
            'email': 'existing@example.com',
            'given_name': 'Test',
            'family_name': 'User'
        }

        result_user, created = GoogleAuthService.get_or_create_user(google_info)

        self.assertFalse(created)
        self.assertEqual(result_user.id, user.id)

        # Should verify email
        result_user.refresh_from_db()
        self.assertTrue(result_user.is_email_verified)

    def test_get_or_create_user_new(self):
        """Test creating new user."""
        google_info = {
            'email': 'newuser@example.com',
            'given_name': 'New',
            'family_name': 'User'
        }

        user, created = GoogleAuthService.get_or_create_user(google_info)

        self.assertTrue(created)
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.first_name, 'New')
        self.assertEqual(user.last_name, 'User')
        self.assertTrue(user.is_email_verified)

    def test_get_or_create_user_no_email(self):
        """Test with missing email."""
        google_info = {
            'given_name': 'Test'
        }

        with self.assertRaises(GoogleOAuthError) as context:
            GoogleAuthService.get_or_create_user(google_info)

        self.assertIn('이메일', str(context.exception))

    def test_get_or_create_user_name_parsing(self):
        """Test parsing full name when first/last name missing."""
        google_info = {
            'email': 'test@example.com',
            'name': 'Full Name'
        }

        user, created = GoogleAuthService.get_or_create_user(google_info)

        self.assertTrue(created)
        self.assertEqual(user.first_name, 'Full')
        self.assertEqual(user.last_name, 'Name')


class GoogleAuthSerializerTest(TestCase):
    """Test GoogleAuthSerializer."""

    @override_settings(SOCIALACCOUNT_PROVIDERS={
        'google': {
            'APP': {
                'client_id': 'test-client-id'
            }
        }
    })
    @patch('accounts.auth.google_auth.GoogleAuthService.verify_google_token')
    @patch('accounts.auth.google_auth.GoogleAuthService.get_or_create_user')
    def test_serializer_valid_token(self, mock_get_user, mock_verify):
        """Test serializer with valid token."""
        mock_user = Mock()
        mock_user.email = 'test@example.com'

        mock_verify.return_value = {'email': 'test@example.com'}
        mock_get_user.return_value = (mock_user, False)

        serializer = GoogleAuthSerializer(data={'token': 'valid-token'})

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.get_user().email, 'test@example.com')
        self.assertFalse(serializer.is_new_user())

    def test_serializer_empty_token(self):
        """Test serializer with empty token."""
        serializer = GoogleAuthSerializer(data={'token': ''})

        self.assertFalse(serializer.is_valid())

    def test_serializer_missing_token(self):
        """Test serializer without token."""
        serializer = GoogleAuthSerializer(data={})

        self.assertFalse(serializer.is_valid())
        self.assertIn('token', serializer.errors)

    @override_settings(SOCIALACCOUNT_PROVIDERS={
        'google': {
            'APP': {
                'client_id': 'test-client-id'
            }
        }
    })
    @patch('accounts.auth.google_auth.GoogleAuthService.verify_google_token')
    def test_serializer_oauth_error(self, mock_verify):
        """Test serializer with OAuth error."""
        mock_verify.side_effect = GoogleOAuthError('Token expired')

        serializer = GoogleAuthSerializer(data={'token': 'expired-token'})

        self.assertFalse(serializer.is_valid())
        self.assertIn('token', serializer.errors)

    @override_settings(SOCIALACCOUNT_PROVIDERS={
        'google': {
            'APP': {
                'client_id': 'test-client-id'
            }
        }
    })
    @patch('accounts.auth.google_auth.GoogleAuthService.verify_google_token')
    @patch('accounts.auth.google_auth.GoogleAuthService.get_or_create_user')
    def test_serializer_new_user(self, mock_get_user, mock_verify):
        """Test serializer with new user."""
        mock_user = Mock()
        mock_user.email = 'newuser@example.com'

        mock_verify.return_value = {'email': 'newuser@example.com'}
        mock_get_user.return_value = (mock_user, True)

        serializer = GoogleAuthSerializer(data={'token': 'valid-token'})

        self.assertTrue(serializer.is_valid())
        self.assertTrue(serializer.is_new_user())

    @override_settings(SOCIALACCOUNT_PROVIDERS={
        'google': {
            'APP': {
                'client_id': 'test-client-id'
            }
        }
    })
    @patch('accounts.auth.google_auth.GoogleAuthService.verify_google_token')
    @patch('accounts.auth.google_auth.GoogleAuthService.get_or_create_user')
    def test_serializer_google_user_info(self, mock_get_user, mock_verify):
        """Test getting Google user info from serializer."""
        mock_user = Mock()
        google_info = {'email': 'test@example.com', 'name': 'Test User'}

        mock_verify.return_value = google_info
        mock_get_user.return_value = (mock_user, False)

        serializer = GoogleAuthSerializer(data={'token': 'valid-token'})

        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.get_google_user_info(), google_info)


class GoogleOAuthViewTest(TestCase):
    """Test Google OAuth view."""

    def setUp(self):
        self.client = APIClient()

    @override_settings(SOCIALACCOUNT_PROVIDERS={
        'google': {
            'APP': {
                'client_id': 'test-client-id'
            }
        }
    })
    @patch('accounts.auth.google_auth.GoogleAuthService.verify_google_token')
    @patch('accounts.auth.google_auth.GoogleAuthService.get_or_create_user')
    def test_google_oauth_success(self, mock_get_user, mock_verify):
        """Test successful Google OAuth."""
        user = User.objects.create_user(
            email='test@example.com',
            is_email_verified=True
        )

        mock_verify.return_value = {'email': 'test@example.com'}
        mock_get_user.return_value = (user, False)

        response = self.client.post('/api/accounts/google-oauth/', {
            'token': 'valid-google-token'
        })

        # Should return 200 or 201
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])

    def test_google_oauth_missing_token(self):
        """Test Google OAuth without token."""
        response = self.client.post('/api/accounts/google-oauth/', {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @override_settings(SOCIALACCOUNT_PROVIDERS={
        'google': {
            'APP': {
                'client_id': 'test-client-id'
            }
        }
    })
    @patch('accounts.auth.google_auth.GoogleAuthService.verify_google_token')
    def test_google_oauth_invalid_token(self, mock_verify):
        """Test Google OAuth with invalid token."""
        mock_verify.side_effect = GoogleOAuthError('Invalid token')

        response = self.client.post('/api/accounts/google-oauth/', {
            'token': 'invalid-token'
        })

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
