"""
Tests for authentication APIs
"""
import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class TestAuthAPI:
    """Test authentication API endpoints"""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def user_data(self):
        return {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'password_confirm': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    @pytest.mark.django_db
    def test_user_registration(self, api_client, user_data):
        """Test user registration"""
        url = reverse('user-register')
        response = api_client.post(url, user_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(username='testuser').exists()
        
        user = User.objects.get(username='testuser')
        assert user.email == 'test@example.com'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.check_password('testpass123')
    
    @pytest.mark.django_db
    def test_user_registration_password_mismatch(self, api_client, user_data):
        """Test user registration with password mismatch"""
        user_data['password_confirm'] = 'differentpass'
        url = reverse('user-register')
        response = api_client.post(url, user_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert not User.objects.filter(username='testuser').exists()
    
    @pytest.mark.django_db
    def test_jwt_token_obtain(self, api_client):
        """Test obtaining JWT tokens"""
        # Create user
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        url = reverse('token_obtain_pair')
        data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'access' in response.data
        assert 'refresh' in response.data
    
    @pytest.mark.django_db
    def test_jwt_token_refresh(self, api_client):
        """Test refreshing JWT tokens"""
        # Create user and get tokens
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        obtain_url = reverse('token_obtain_pair')
        obtain_data = {
            'username': 'testuser',
            'password': 'testpass123'
        }
        obtain_response = api_client.post(obtain_url, obtain_data, format='json')
        refresh_token = obtain_response.data['refresh']
        
        # Test refresh
        refresh_url = reverse('token_refresh')
        refresh_data = {'refresh': refresh_token}
        refresh_response = api_client.post(refresh_url, refresh_data, format='json')
        
        assert refresh_response.status_code == status.HTTP_200_OK
        assert 'access' in refresh_response.data


class TestProfileAPI:
    """Test profile API endpoints"""
    
    @pytest.fixture
    def user(self, db):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User'
        )
    
    @pytest.fixture
    def authenticated_client(self, user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client
    
    @pytest.mark.django_db
    def test_get_profile(self, authenticated_client, user):
        """Test getting user profile"""
        url = reverse('profile')
        response = authenticated_client.get(url)
        
        assert response.status_code == status.HTTP_200_OK
        assert response.data['username'] == user.username
        assert response.data['email'] == user.email
        assert response.data['first_name'] == user.first_name
        assert response.data['last_name'] == user.last_name
    
    @pytest.mark.django_db
    def test_update_profile(self, authenticated_client, user):
        """Test updating user profile"""
        url = reverse('profile')
        data = {
            'username': user.username,
            'email': user.email,
            'first_name': 'Updated',
            'last_name': 'Name',
            'timezone': 'America/New_York',
            'notification_enabled': False
        }
        response = authenticated_client.put(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        
        user.refresh_from_db()
        assert user.first_name == 'Updated'
        assert user.last_name == 'Name'
        assert user.timezone == 'America/New_York'
        assert user.notification_enabled is False
    
    @pytest.mark.django_db
    def test_profile_requires_authentication(self):
        """Test that profile endpoint requires authentication"""
        client = APIClient()
        url = reverse('profile')
        response = client.get(url)
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED