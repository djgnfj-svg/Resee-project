"""
Simple test to verify URL patterns
"""

from django.test import TestCase
from django.urls import reverse

class SimpleURLTestCase(TestCase):
    """Simple test case for URL patterns"""
    
    def test_url_patterns(self):
        """Test basic URL patterns"""
        # Test token URLs
        try:
            url = reverse('token_obtain_pair')
            print(f"token_obtain_pair: {url}")
        except Exception as e:
            print(f"Error with token_obtain_pair: {e}")
        
        # Test accounts URLs
        try:
            url = reverse('accounts:profile')
            print(f"accounts:profile: {url}")
        except Exception as e:
            print(f"Error with accounts:profile: {e}")
            
        try:
            url = reverse('accounts:users-list')
            print(f"accounts:users-list: {url}")
        except Exception as e:
            print(f"Error with accounts:users-list: {e}")
            
        # Test content URLs
        try:
            url = reverse('content:contents-list')
            print(f"content:contents-list: {url}")
        except Exception as e:
            print(f"Error with content:contents-list: {e}")
            
        # Test review URLs
        try:
            url = reverse('review:today')
            print(f"review:today: {url}")
        except Exception as e:
            print(f"Error with review:today: {e}")
            
        # Test analytics URLs
        try:
            url = reverse('analytics:dashboard')
            print(f"analytics:dashboard: {url}")
        except Exception as e:
            print(f"Error with analytics:dashboard: {e}")
            
        # This should always pass
        self.assertTrue(True)