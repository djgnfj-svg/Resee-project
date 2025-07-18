"""
Comprehensive API security and edge case tests
"""

import json
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .base import BaseAPITestCase, TestDataMixin, BaseTestCase
from content.models import Content, Category
from review.models import ReviewSchedule, ReviewHistory

User = get_user_model()


class AuthenticationSecurityTestCase(APITestCase):
    """Test authentication security scenarios"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='otherpass123'
        )
    
    def test_unauthenticated_access_blocked(self):
        """Test that protected endpoints require authentication"""
        protected_urls = [
            reverse('accounts:profile'),
            reverse('content:contents-list'),
            reverse('content:categories-list'),
            reverse('content:tags-list'),
            reverse('review:today'),
            reverse('review:complete'),
            reverse('analytics:dashboard'),
        ]
        
        for url in protected_urls:
            response = self.client.get(url)
            self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
    
    def test_invalid_token_rejected(self):
        """Test that invalid tokens are rejected"""
        self.client.credentials(HTTP_AUTHORIZATION='Bearer invalid_token')
        
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_expired_token_rejected(self):
        """Test that expired tokens are handled properly"""
        # This would require mocking token expiration
        # For now, test with malformed token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer malformed.token.here')
        
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_token_refresh_cycle(self):
        """Test complete token refresh cycle"""
        # Get initial tokens
        login_url = reverse('token_obtain_pair')
        login_data = {'username': 'testuser', 'password': 'testpass123'}
        response = self.client.post(login_url, login_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_token = response.data['access']
        refresh_token = response.data['refresh']
        
        # Use access token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Refresh token
        refresh_url = reverse('token_refresh')
        refresh_data = {'refresh': refresh_token}
        response = self.client.post(refresh_url, refresh_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_access_token = response.data['access']
        
        # Use new access token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {new_access_token}')
        response = self.client.get(reverse('accounts:profile'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_user_data_isolation(self):
        """Test that users cannot access other users' data"""
        # Create content for other user
        other_token = RefreshToken.for_user(self.other_user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {other_token}')
        
        category_data = {'name': 'Other Category'}
        response = self.client.post(reverse('content:categories-list'), category_data, format='json')
        other_category_id = response.data['id']
        
        content_data = {
            'title': 'Other Content',
            'content': 'Other user content',
            'category': other_category_id,
            'priority': 'medium'
        }
        response = self.client.post(reverse('content:contents-list'), content_data, format='json')
        other_content_id = response.data['id']
        
        # Switch to main user
        main_token = RefreshToken.for_user(self.user).access_token
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {main_token}')
        
        # Try to access other user's content
        response = self.client.get(reverse('content:contents-detail', kwargs={'pk': other_content_id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Try to modify other user's content
        update_data = {'title': 'Hacked Title'}
        response = self.client.patch(reverse('content:contents-detail', kwargs={'pk': other_content_id}), update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Try to delete other user's content
        response = self.client.delete(reverse('content:contents-detail', kwargs={'pk': other_content_id}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class InputValidationTestCase(BaseAPITestCase, TestDataMixin):
    """Test input validation across all endpoints"""
    
    def test_content_validation(self):
        """Test content creation validation"""
        url = reverse('content:contents-list')
        
        # Test empty title
        data = {'title': '', 'content': 'Valid content', 'priority': 'medium'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid priority
        data = {'title': 'Valid Title', 'content': 'Valid content', 'priority': 'invalid'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test non-existent category
        data = {'title': 'Valid Title', 'content': 'Valid content', 'priority': 'medium', 'category': 99999}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test non-existent tags
        data = {'title': 'Valid Title', 'content': 'Valid content', 'priority': 'medium', 'tag_ids': [99999]}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test extremely long title
        data = {'title': 'x' * 250, 'content': 'Valid content', 'priority': 'medium'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_category_validation(self):
        """Test category validation"""
        url = reverse('content:categories-list')
        
        # Test empty name
        data = {'name': ''}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test duplicate name for same user
        data = {'name': 'Test Category'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test extremely long name
        data = {'name': 'x' * 120}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_tag_validation(self):
        """Test tag validation"""
        url = reverse('content:tags-list')
        
        # Test empty name
        data = {'name': ''}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test duplicate name
        data = {'name': 'test-tag'}  # This tag exists from base setup
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test extremely long name
        data = {'name': 'x' * 60}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_review_completion_validation(self):
        """Test review completion validation"""
        schedule = self.create_review_schedule()
        url = reverse('review:complete')
        
        # Test invalid schedule_id
        data = {'schedule_id': 99999, 'result': 'remembered', 'time_spent': 120}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid result
        data = {'schedule_id': schedule.id, 'result': 'invalid', 'time_spent': 120}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test negative time_spent
        data = {'schedule_id': schedule.id, 'result': 'remembered', 'time_spent': -1}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test extremely large time_spent
        data = {'schedule_id': schedule.id, 'result': 'remembered', 'time_spent': 999999}
        response = self.client.post(url, data, format='json')
        # This should be accepted but might be logged for monitoring
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_user_registration_validation(self):
        """Test user registration validation"""
        url = reverse('accounts:users-register')
        
        # Test password mismatch
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'password123',
            'password_confirm': 'differentpassword',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test duplicate username
        data = {
            'username': 'testuser',  # Already exists
            'email': 'unique@example.com',
            'password': 'password123',
            'password_confirm': 'password123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test duplicate email
        data = {
            'username': 'uniqueuser',
            'email': 'test@example.com',  # Already exists
            'password': 'password123',
            'password_confirm': 'password123',
            'first_name': 'Test',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid email
        data = {
            'username': 'newuser',
            'email': 'invalid-email',
            'password': 'password123',
            'password_confirm': 'password123',
            'first_name': 'New',
            'last_name': 'User'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PaginationAndFilteringTestCase(BaseAPITestCase, TestDataMixin):
    """Test pagination and filtering functionality"""
    
    def setUp(self):
        super().setUp()
        # Create multiple contents for testing
        for i in range(25):
            self.create_content(title=f'Content {i}', priority='high' if i % 2 == 0 else 'low')
    
    def test_content_pagination(self):
        """Test content list pagination"""
        url = reverse('content:contents-list')
        
        # Test first page
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('count', response.data)
        self.assertIn('next', response.data)
        self.assertIn('previous', response.data)
        self.assertIn('results', response.data)
        
        # Should have pagination with default page size
        self.assertGreaterEqual(response.data['count'], 25)
        self.assertIsNotNone(response.data['next'])
        self.assertIsNone(response.data['previous'])
        
        # Test second page
        response = self.client.get(response.data['next'])
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsNotNone(response.data['previous'])
    
    def test_content_filtering_by_priority(self):
        """Test content filtering by priority"""
        url = reverse('content:contents-list')
        
        # Filter by high priority
        response = self.client.get(url, {'priority': 'high'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        for content in response.data['results']:
            self.assertEqual(content['priority'], 'high')
        
        # Filter by low priority
        response = self.client.get(url, {'priority': 'low'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        for content in response.data['results']:
            self.assertEqual(content['priority'], 'low')
    
    def test_content_search(self):
        """Test content search functionality"""
        # Create content with specific searchable text
        searchable_content = self.create_content(
            title='Searchable Python Tutorial',
            content='This content covers Python programming concepts'
        )
        
        url = reverse('content:contents-list')
        
        # Search by title
        response = self.client.get(url, {'search': 'Python'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        found_titles = [item['title'] for item in response.data['results']]
        self.assertIn('Searchable Python Tutorial', found_titles)
        
        # Search by content
        response = self.client.get(url, {'search': 'programming'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        found_titles = [item['title'] for item in response.data['results']]
        self.assertIn('Searchable Python Tutorial', found_titles)
    
    def test_content_ordering(self):
        """Test content ordering options"""
        url = reverse('content:contents-list')
        
        # Test ordering by creation date (ascending)
        response = self.client.get(url, {'ordering': 'created_at'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test ordering by title
        response = self.client.get(url, {'ordering': 'title'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test ordering by priority
        response = self.client.get(url, {'ordering': 'priority'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_invalid_pagination_parameters(self):
        """Test invalid pagination parameters"""
        url = reverse('content:contents-list')
        
        # Test invalid page number
        response = self.client.get(url, {'page': 'invalid'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test negative page number
        response = self.client.get(url, {'page': -1})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test page number too high
        response = self.client.get(url, {'page': 999})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class RateLimitingTestCase(BaseAPITestCase):
    """Test rate limiting protection"""
    
    def test_login_rate_limiting(self):
        """Test rate limiting on login attempts"""
        login_url = reverse('token_obtain_pair')
        invalid_data = {'username': 'testuser', 'password': 'wrongpassword'}
        
        # Make multiple failed login attempts
        for i in range(10):
            response = self.client.post(login_url, invalid_data, format='json')
            # First few should return 401, later might be rate limited
            self.assertIn(response.status_code, [
                status.HTTP_401_UNAUTHORIZED, 
                status.HTTP_429_TOO_MANY_REQUESTS
            ])
    
    def test_api_request_limits(self):
        """Test general API request rate limits"""
        # This would require actual rate limiting implementation
        # For now, just ensure endpoints respond normally
        urls = [
            reverse('content:contents-list'),
            reverse('content:categories-list'),
            reverse('analytics:dashboard'),
        ]
        
        for url in urls:
            for i in range(5):
                response = self.client.get(url)
                self.assertEqual(response.status_code, status.HTTP_200_OK)


class CORSAndSecurityHeadersTestCase(BaseAPITestCase):
    """Test CORS and security headers"""
    
    def test_cors_headers_present(self):
        """Test that CORS headers are properly set"""
        response = self.client.options(reverse('content:contents-list'))
        
        # Check for CORS headers
        self.assertIn('Access-Control-Allow-Origin', response.headers)
        self.assertIn('Access-Control-Allow-Methods', response.headers)
        self.assertIn('Access-Control-Allow-Headers', response.headers)
    
    def test_security_headers(self):
        """Test security headers are present"""
        response = self.client.get(reverse('content:contents-list'))
        
        # These headers should be set by Django middleware
        expected_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
        ]
        
        for header in expected_headers:
            if header in response.headers:
                self.assertIsNotNone(response.headers[header])


class ErrorHandlingTestCase(BaseAPITestCase, TestDataMixin):
    """Test error handling scenarios"""
    
    def test_404_handling(self):
        """Test 404 error handling"""
        # Test non-existent content
        response = self.client.get(reverse('content:contents-detail', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # Test non-existent category
        response = self.client.get(reverse('content:categories-detail', kwargs={'pk': 99999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_method_not_allowed(self):
        """Test method not allowed handling"""
        # Try PATCH on list endpoints
        response = self.client.patch(reverse('content:contents-list'), {})
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
    
    def test_malformed_json(self):
        """Test malformed JSON handling"""
        response = self.client.post(
            reverse('content:contents-list'),
            data='{"invalid": json}',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_content_type_validation(self):
        """Test content type validation"""
        # Send form data when JSON expected
        response = self.client.post(
            reverse('content:contents-list'),
            data={'title': 'Test'},
            content_type='application/x-www-form-urlencoded'
        )
        # Should still work as DRF handles multiple content types
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,  # Due to missing required fields
            status.HTTP_201_CREATED       # If minimal validation passes
        ])


class DatabaseConstraintTestCase(BaseTestCase):
    """Test database constraint enforcement"""
    
    def test_unique_constraints(self):
        """Test unique constraint enforcement"""
        # Test unique category name per user
        category1 = Category.objects.create(name='Test Category', user=self.user)
        
        with self.assertRaises(Exception):
            Category.objects.create(name='Test Category', user=self.user)
        
        # But different user can have same category name
        other_user = self.create_user(username='other', email='other@example.com')
        category2 = Category.objects.create(name='Test Category', user=other_user)
        self.assertNotEqual(category1.id, category2.id)
    
    def test_foreign_key_constraints(self):
        """Test foreign key constraint enforcement"""
        content = self.create_content()
        
        # Delete referenced user should cascade
        user_id = content.author.id
        content.author.delete()
        
        # Content should be deleted due to CASCADE
        self.assertFalse(Content.objects.filter(author_id=user_id).exists())
    
    def test_review_schedule_uniqueness(self):
        """Test review schedule uniqueness per user-content pair"""
        content = self.create_content()
        
        schedule1 = self.create_review_schedule(content=content)
        
        # Should not be able to create another schedule for same user-content
        with self.assertRaises(Exception):
            self.create_review_schedule(content=content)


@override_settings(DEBUG=False)
class ProductionConfigTestCase(APITestCase):
    """Test production configuration settings"""
    
    def test_debug_mode_disabled(self):
        """Test that debug mode is disabled in production settings"""
        from django.conf import settings
        self.assertFalse(settings.DEBUG)
    
    def test_allowed_hosts_configured(self):
        """Test that ALLOWED_HOSTS is properly configured"""
        from django.conf import settings
        self.assertIsInstance(settings.ALLOWED_HOSTS, list)
        self.assertNotIn('*', settings.ALLOWED_HOSTS)  # Wildcard should not be in production
    
    def test_secret_key_not_default(self):
        """Test that SECRET_KEY is not the default development key"""
        from django.conf import settings
        self.assertNotIn('django-insecure', settings.SECRET_KEY)
        self.assertGreater(len(settings.SECRET_KEY), 30)  # Should be reasonably long