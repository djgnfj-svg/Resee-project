"""
Test cases for analytics application
"""
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from content.models import Category, Content
from review.models import ReviewHistory

User = get_user_model()


class DashboardStatsViewTest(APITestCase):
    """Test DashboardStatsView API endpoint"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_email_verified = True
        self.user.save()

        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

        # Create test data
        self.category = Category.objects.create(
            name='Test Category',
            user=self.user
        )

        self.content = Content.objects.create(
            title='Test Content',
            content='Test content body',
            author=self.user,
            category=self.category
        )


    def test_dashboard_stats_view_success(self):
        """Test successful dashboard statistics retrieval"""
        url = reverse('analytics:dashboard-stats')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Check response structure
        data = response.data
        required_fields = [
            'today_reviews', 'pending_reviews', 'total_content',
            'success_rate', 'total_reviews_30_days'
        ]

        for field in required_fields:
            self.assertIn(field, data)

        # Check basic values
        self.assertEqual(data['total_content'], 1)
        self.assertIsInstance(data['today_reviews'], int)
        self.assertIsInstance(data['pending_reviews'], int)
        self.assertIsInstance(data['success_rate'], (int, float))
        self.assertIsInstance(data['total_reviews_30_days'], int)

    def test_dashboard_stats_with_review_data(self):
        """Test dashboard stats with actual review history"""
        # Create review history
        for i in range(5):
            ReviewHistory.objects.create(
                user=self.user,
                content=self.content,
                result='remembered' if i < 3 else 'forgot',
                review_date=timezone.now() - timedelta(days=i)
            )

        url = reverse('analytics:dashboard-stats')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.data

        # Should have some review data now
        self.assertEqual(data['total_reviews_30_days'], 5)
        self.assertGreaterEqual(data['success_rate'], 0)
        self.assertLessEqual(data['success_rate'], 100)

    def test_dashboard_stats_unauthenticated(self):
        """Test dashboard stats without authentication"""
        self.client.credentials()  # Clear authentication

        url = reverse('analytics:dashboard-stats')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)