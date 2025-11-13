"""
Tests for authentication views.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class EmailTokenObtainPairViewTest(TestCase):
    """Test JWT token login."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )

    def test_login_success(self):
        """Test successful login with valid credentials."""
        response = self.client.post('/api/auth/token/', {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_invalid_email(self):
        """Test login with non-existent email."""
        response = self.client.post('/api/auth/token/', {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        })
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED])

    def test_login_invalid_password(self):
        """Test login with wrong password."""
        response = self.client.post('/api/auth/token/', {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED])

    def test_login_missing_email(self):
        """Test login without email field."""
        response = self.client.post('/api/auth/token/', {
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_missing_password(self):
        """Test login without password field."""
        response = self.client.post('/api/auth/token/', {
            'email': 'test@example.com'
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserRegistrationTest(TestCase):
    """Test user registration."""

    def setUp(self):
        self.client = APIClient()

    @override_settings(ENFORCE_EMAIL_VERIFICATION=False)
    def test_registration_success(self):
        """Test successful registration."""
        response = self.client.post('/api/accounts/users/', {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'terms_agreed': True,
            'privacy_agreed': True
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('data', response.data)
        self.assertIn('user', response.data['data'])
        self.assertIn('requires_email_verification', response.data['data'])

        # Check user was created
        user = User.objects.get(email='newuser@example.com')
        self.assertIsNotNone(user)
        self.assertTrue(user.check_password('newpass123'))

    @override_settings(ENFORCE_EMAIL_VERIFICATION=False)
    def test_registration_via_register_endpoint(self):
        """Test registration via legacy /register/ endpoint."""
        response = self.client.post('/api/accounts/users/register/', {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'terms_agreed': True,
            'privacy_agreed': True
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_registration_password_mismatch(self):
        """Test registration with mismatched passwords."""
        response = self.client.post('/api/accounts/users/', {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'differentpass',
            'terms_agreed': True,
            'privacy_agreed': True
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_duplicate_email(self):
        """Test registration with existing email."""
        User.objects.create_user(
            email='existing@example.com',
            password='pass123'
        )

        response = self.client.post('/api/accounts/users/', {
            'email': 'existing@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'terms_agreed': True,
            'privacy_agreed': True
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_invalid_email(self):
        """Test registration with invalid email format."""
        response = self.client.post('/api/accounts/users/', {
            'email': 'invalid-email',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'terms_agreed': True,
            'privacy_agreed': True
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_missing_email(self):
        """Test registration without email."""
        response = self.client.post('/api/accounts/users/', {
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'terms_agreed': True,
            'privacy_agreed': True
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_weak_password(self):
        """Test registration with weak password."""
        response = self.client.post('/api/accounts/users/', {
            'email': 'newuser@example.com',
            'password': '123',
            'password_confirm': '123',
            'terms_agreed': True,
            'privacy_agreed': True
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registration_without_terms_agreement(self):
        """Test registration without terms agreement."""
        response = self.client.post('/api/accounts/users/', {
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'terms_agreed': False,
            'privacy_agreed': True
        })
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UserMeEndpointTest(TestCase):
    """Test /users/me/ endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        self.client.force_authenticate(user=self.user)

    def test_get_current_user(self):
        """Test getting current user information."""
        response = self.client.get('/api/accounts/users/me/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertIn('subscription', response.data)

    def test_get_current_user_unauthenticated(self):
        """Test getting current user without authentication."""
        self.client.logout()
        response = self.client.get('/api/accounts/users/me/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_account_success(self):
        """Test successful account deletion."""
        response = self.client.delete('/api/accounts/users/me/', {
            'password': 'testpass123',
            'confirmation': 'DELETE'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check user was deleted
        self.assertFalse(User.objects.filter(email='test@example.com').exists())

    def test_delete_account_wrong_password(self):
        """Test account deletion with wrong password."""
        response = self.client.delete('/api/accounts/users/me/', {
            'password': 'wrongpass',
            'confirmation': 'DELETE'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Check user was not deleted
        self.assertTrue(User.objects.filter(email='test@example.com').exists())

    def test_delete_account_wrong_confirmation(self):
        """Test account deletion with wrong confirmation."""
        response = self.client.delete('/api/accounts/users/me/', {
            'password': 'testpass123',
            'confirmation': 'WRONG'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Check user was not deleted
        self.assertTrue(User.objects.filter(email='test@example.com').exists())

    def test_delete_account_missing_fields(self):
        """Test account deletion without required fields."""
        response = self.client.delete('/api/accounts/users/me/', {
            'password': 'testpass123'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_account_unauthenticated(self):
        """Test account deletion without authentication."""
        self.client.logout()
        response = self.client.delete('/api/accounts/users/me/', {
            'password': 'testpass123',
            'confirmation': 'DELETE'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserListTest(TestCase):
    """Test user list endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(
            email='admin@example.com',
            password='adminpass123'
        )
        self.user = User.objects.create_user(
            email='user@example.com',
            password='userpass123'
        )

    def test_list_users_as_admin(self):
        """Test listing users as admin."""
        self.client.force_authenticate(user=self.admin)
        response = self.client.get('/api/accounts/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)

    def test_list_users_as_regular_user(self):
        """Test listing users as regular user."""
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/accounts/users/')
        # Regular users can also list (filtered by permissions)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_403_FORBIDDEN])

    def test_list_users_unauthenticated(self):
        """Test listing users without authentication."""
        response = self.client.get('/api/accounts/users/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
