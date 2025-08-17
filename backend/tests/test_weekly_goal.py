"""
Test weekly goal functionality
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


@pytest.mark.django_db
class TestWeeklyGoal:
    """Test weekly goal setting and retrieval"""
    
    @pytest.fixture
    def api_client(self):
        return APIClient()
    
    @pytest.fixture
    def user(self):
        user = User.objects.create_user(
            email='goaluser@test.com',
            password='testpass123'
        )
        user.is_active = True
        user.save()
        return user
    
    @pytest.fixture
    def authenticated_client(self, api_client, user):
        api_client.force_authenticate(user=user)
        return api_client
    
    def test_default_weekly_goal(self, authenticated_client, user):
        """Test that new users have default weekly goal of 7"""
        response = authenticated_client.get('/api/accounts/weekly-goal/')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['weekly_goal'] == 7
        
    def test_update_weekly_goal(self, authenticated_client, user):
        """Test updating weekly goal"""
        # Update to 15
        response = authenticated_client.put('/api/accounts/weekly-goal/', {
            'weekly_goal': 15
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['weekly_goal'] == 15
        
        # Verify it's saved
        user.refresh_from_db()
        assert user.weekly_goal == 15
        
    def test_weekly_goal_validation(self, authenticated_client, user):
        """Test weekly goal validation"""
        # Test minimum value
        response = authenticated_client.put('/api/accounts/weekly-goal/', {
            'weekly_goal': 0
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Test maximum value
        response = authenticated_client.put('/api/accounts/weekly-goal/', {
            'weekly_goal': 101
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        
        # Test valid range
        response = authenticated_client.put('/api/accounts/weekly-goal/', {
            'weekly_goal': 50
        })
        assert response.status_code == status.HTTP_200_OK
        assert response.data['weekly_goal'] == 50
        
    def test_weekly_goal_in_analytics(self, authenticated_client, user):
        """Test that weekly goal appears in analytics data"""
        # Set custom goal
        authenticated_client.put('/api/accounts/weekly-goal/', {
            'weekly_goal': 20
        })
        
        # Get analytics
        response = authenticated_client.get('/api/analytics/advanced/')
        assert response.status_code == status.HTTP_200_OK
        
        metrics = response.data['performance_metrics']
        assert metrics['weeklyGoal'] == 20
        
    def test_weekly_goal_requires_auth(self, api_client):
        """Test that weekly goal endpoints require authentication"""
        # Try to get goal without auth
        response = api_client.get('/api/accounts/weekly-goal/')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        
        # Try to update without auth
        response = api_client.put('/api/accounts/weekly-goal/', {
            'weekly_goal': 10
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED