"""
Test cases for legal views import fixes and functionality
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from unittest.mock import patch, Mock

from .legal_views import CreateConsentView, CookieConsentView, withdraw_consent
from .utils import collect_client_info


User = get_user_model()


class LegalViewsImportTestCase(TestCase):
    """Test cases for legal views import fixes"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
    
    def test_legal_models_import(self):
        """Test that legal models are properly imported"""
        # These imports should work without error
        from accounts.legal_models import (
            CookieConsent, DataDeletionRequest, DataExportRequest,
            LegalDocument, UserConsent
        )
        
        # Verify models are accessible
        self.assertTrue(hasattr(CookieConsent, '_meta'))
        self.assertTrue(hasattr(UserConsent, '_meta'))
        self.assertTrue(hasattr(LegalDocument, '_meta'))
    
    def test_legal_serializers_import(self):
        """Test that legal serializers are properly imported"""
        from accounts.legal_serializers import (
            CookieConsentSerializer, CreateConsentSerializer,
            UserConsentSerializer
        )
        
        # Verify serializers are accessible
        self.assertTrue(hasattr(CookieConsentSerializer, 'Meta'))
        self.assertTrue(hasattr(CreateConsentSerializer, 'Meta'))
        self.assertTrue(hasattr(UserConsentSerializer, 'Meta'))
    
    def test_utils_import_in_views(self):
        """Test that utils functions are properly imported in views"""
        # This should not raise ImportError
        from accounts.legal_views import collect_client_info
        
        # Verify function is callable
        request = self.factory.get('/')
        info = collect_client_info(request)
        
        self.assertIsInstance(info, dict)
        self.assertIn('ip_address', info)
        self.assertIn('user_agent', info)
    
    def test_collect_client_info_usage_in_create_consent(self):
        """Test that collect_client_info is used in CreateConsentView"""
        view = CreateConsentView()
        request = self.factory.post('/', {
            'consent_type': 'privacy_policy',
            'is_consented': True
        })
        request.user = self.user
        
        # Mock the collect_client_info to verify it's called
        with patch('accounts.legal_views.collect_client_info') as mock_collect:
            mock_collect.return_value = {
                'ip_address': '127.0.0.1',
                'user_agent': 'TestAgent'
            }
            
            # Mock LegalDocument.objects.get to prevent DoesNotExist
            with patch('accounts.legal_views.LegalDocument.objects.get') as mock_doc:
                mock_doc.return_value = Mock(version='1.0')
                
                # Mock UserConsent.objects.update_or_create
                with patch('accounts.legal_views.UserConsent.objects.update_or_create') as mock_consent:
                    mock_consent.return_value = (Mock(id=1), True)
                    
                    response = view.post(request)
                    
                    # Verify collect_client_info was called
                    mock_collect.assert_called_once_with(request)
    
    def test_collect_client_info_usage_in_cookie_consent(self):
        """Test that collect_client_info is used in CookieConsentView"""
        view = CookieConsentView()
        request = self.factory.post('/', {
            'analytics_cookies': True,
            'marketing_cookies': False,
            'functional_cookies': True
        })
        request.user = self.user
        
        with patch('accounts.legal_views.collect_client_info') as mock_collect:
            mock_collect.return_value = {
                'ip_address': '192.168.1.1',
                'user_agent': 'Mozilla/5.0'
            }
            
            with patch('accounts.legal_views.CookieConsent.objects.create') as mock_create:
                mock_create.return_value = Mock(id=1)
                
                response = view.post(request)
                
                # Verify collect_client_info was called
                mock_collect.assert_called_once_with(request)
    
    def test_withdraw_consent_client_info(self):
        """Test that collect_client_info is used in withdraw_consent"""
        request = self.factory.post('/', {'consent_type': 'marketing'})
        request.user = self.user
        
        with patch('accounts.legal_views.collect_client_info') as mock_collect:
            mock_collect.return_value = {
                'ip_address': '10.0.0.1',
                'user_agent': 'TestClient'
            }
            
            # Mock UserConsent.objects.filter().latest()
            mock_consent = Mock(document_version='1.0')
            with patch('accounts.legal_views.UserConsent.objects.filter') as mock_filter:
                mock_filter.return_value.latest.return_value = mock_consent
                
                with patch('accounts.legal_views.UserConsent.objects.create') as mock_create:
                    response = withdraw_consent(request)
                    
                    # Verify collect_client_info was called
                    mock_collect.assert_called_once_with(request)
    
    def test_no_gdpr_service_dependency(self):
        """Test that GDPRService import has been removed"""
        # This should not raise ImportError even though GDPRService doesn't exist
        import accounts.legal_views
        
        # Verify GDPRService is not imported
        self.assertFalse(hasattr(accounts.legal_views, 'GDPRService'))
    
    def test_view_classes_instantiation(self):
        """Test that view classes can be instantiated without import errors"""
        # These should not raise ImportError
        from accounts.legal_views import (
            LegalDocumentDetailView,
            CreateConsentView,
            CookieConsentView,
            DataDeletionRequestView,
            DataExportRequestView
        )
        
        # Verify classes can be instantiated
        self.assertIsNotNone(LegalDocumentDetailView())
        self.assertIsNotNone(CreateConsentView())
        self.assertIsNotNone(CookieConsentView())
        self.assertIsNotNone(DataDeletionRequestView())
        self.assertIsNotNone(DataExportRequestView())