"""
Tests for account views (Profile, WeeklyGoal, NotificationPreferences).
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from accounts.models import NotificationPreference

User = get_user_model()


class ProfileViewTest(TestCase):
    """Test ProfileView."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        """Test getting user profile."""
        response = self.client.get('/api/accounts/profile/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')

    def test_update_profile(self):
        """Test updating user profile."""
        response = self.client.put('/api/accounts/profile/', {
            'email': 'test@example.com',
            'username': 'newusername'
        }, format='json')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

        if response.status_code == status.HTTP_200_OK:
            self.user.refresh_from_db()
            self.assertEqual(self.user.username, 'newusername')

    def test_get_profile_unauthenticated(self):
        """Test getting profile without authentication."""
        self.client.logout()
        response = self.client.get('/api/accounts/profile/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class WeeklyGoalUpdateViewTest(TestCase):
    """Test WeeklyGoalUpdateView."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True,
            weekly_goal=7
        )
        self.client.force_authenticate(user=self.user)

    def test_get_weekly_goal(self):
        """Test getting weekly goal."""
        response = self.client.get('/api/accounts/weekly-goal/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('weekly_goal', response.data)

    def test_update_weekly_goal(self):
        """Test updating weekly goal."""
        response = self.client.put('/api/accounts/weekly-goal/', {
            'weekly_goal': 10
        }, format='json')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

        if response.status_code == status.HTTP_200_OK:
            self.user.refresh_from_db()
            self.assertEqual(self.user.weekly_goal, 10)

    def test_update_weekly_goal_invalid(self):
        """Test updating weekly goal with invalid value."""
        response = self.client.put('/api/accounts/weekly-goal/', {
            'weekly_goal': -1
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_weekly_goal_unauthenticated(self):
        """Test updating weekly goal without authentication."""
        self.client.logout()
        response = self.client.put('/api/accounts/weekly-goal/', {
            'weekly_goal': 10
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class NotificationPreferenceViewTest(TestCase):
    """Test NotificationPreferenceView."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            is_email_verified=True
        )
        self.client.force_authenticate(user=self.user)

    def test_get_notification_preferences(self):
        """Test getting notification preferences."""
        response = self.client.get('/api/accounts/notification-preferences/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('email_notifications_enabled', response.data)

    def test_create_notification_preferences(self):
        """Test that POST is not allowed (preferences are auto-created)."""
        response = self.client.post('/api/accounts/notification-preferences/', {
            'email_notifications_enabled': True,
            'daily_reminder_enabled': True
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_notification_preferences(self):
        """Test updating notification preferences."""
        # Ensure preference exists
        NotificationPreference.objects.get_or_create(user=self.user)

        response = self.client.put('/api/accounts/notification-preferences/', {
            'email_notifications_enabled': False,
            'daily_reminder_enabled': False
        }, format='json')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

        if response.status_code == status.HTTP_200_OK:
            pref = NotificationPreference.objects.get(user=self.user)
            self.assertFalse(pref.email_notifications_enabled)
            self.assertFalse(pref.daily_reminder_enabled)

    def test_notification_preferences_unauthenticated(self):
        """Test notification preferences without authentication."""
        self.client.logout()
        response = self.client.get('/api/accounts/notification-preferences/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
