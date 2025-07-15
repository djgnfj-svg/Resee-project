"""
Debug test to see error details
"""
import pytest
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()


@pytest.mark.django_db
def test_debug_profile_update():
    """Debug profile update"""
    user = User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123',
        first_name='Test',
        last_name='User'
    )
    
    client = APIClient()
    client.force_authenticate(user=user)
    
    url = reverse('profile')
    data = {
        'first_name': 'Updated',
        'last_name': 'Name',
        'timezone': 'America/New_York',
        'notification_enabled': False
    }
    response = client.put(url, data, format='json')
    
    print(f"Status: {response.status_code}")
    print(f"Data: {response.data}")
    
    assert False  # Force output