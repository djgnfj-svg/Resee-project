"""
Test cases for accounts/utils.py module
"""
from django.http import HttpRequest
from django.test import TestCase, RequestFactory
from unittest.mock import Mock

from .utils import get_client_ip, get_user_agent, collect_client_info


class UtilsTestCase(TestCase):
    """Test cases for utility functions"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.factory = RequestFactory()
    
    def test_get_client_ip_from_x_forwarded_for(self):
        """Test IP extraction from X-Forwarded-For header"""
        request = self.factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '192.168.1.1, 10.0.0.1'
        
        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')
    
    def test_get_client_ip_from_remote_addr(self):
        """Test IP extraction from REMOTE_ADDR"""
        request = self.factory.get('/')
        request.META['REMOTE_ADDR'] = '127.0.0.1'
        
        ip = get_client_ip(request)
        self.assertEqual(ip, '127.0.0.1')
    
    def test_get_client_ip_empty_fallback(self):
        """Test IP extraction with no headers"""
        request = self.factory.get('/')
        
        ip = get_client_ip(request)
        self.assertEqual(ip, '')
    
    def test_get_client_ip_strips_whitespace(self):
        """Test IP extraction strips whitespace"""
        request = self.factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = ' 192.168.1.1 , 10.0.0.1'
        
        ip = get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')
    
    def test_get_user_agent_present(self):
        """Test User-Agent extraction when present"""
        request = self.factory.get('/')
        request.META['HTTP_USER_AGENT'] = 'Mozilla/5.0 (Test Browser)'
        
        user_agent = get_user_agent(request)
        self.assertEqual(user_agent, 'Mozilla/5.0 (Test Browser)')
    
    def test_get_user_agent_missing(self):
        """Test User-Agent extraction when missing"""
        request = self.factory.get('/')
        
        user_agent = get_user_agent(request)
        self.assertEqual(user_agent, '')
    
    def test_collect_client_info_complete(self):
        """Test complete client info collection"""
        request = self.factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '192.168.1.1'
        request.META['HTTP_USER_AGENT'] = 'Test Browser'
        
        info = collect_client_info(request)
        
        self.assertIsInstance(info, dict)
        self.assertEqual(info['ip_address'], '192.168.1.1')
        self.assertEqual(info['user_agent'], 'Test Browser')
    
    def test_collect_client_info_empty(self):
        """Test client info collection with empty headers"""
        request = self.factory.get('/')
        
        info = collect_client_info(request)
        
        self.assertIsInstance(info, dict)
        self.assertEqual(info['ip_address'], '')
        self.assertEqual(info['user_agent'], '')
    
    def test_collect_client_info_keys(self):
        """Test client info dictionary has correct keys"""
        request = self.factory.get('/')
        
        info = collect_client_info(request)
        
        self.assertIn('ip_address', info)
        self.assertIn('user_agent', info)
        self.assertEqual(len(info.keys()), 2)
    
    def test_type_hints_compatibility(self):
        """Test that functions work with HttpRequest type"""
        request = HttpRequest()
        request.META = {
            'HTTP_X_FORWARDED_FOR': '127.0.0.1',
            'HTTP_USER_AGENT': 'TestAgent'
        }
        
        # These should not raise type errors
        ip = get_client_ip(request)
        agent = get_user_agent(request)
        info = collect_client_info(request)
        
        self.assertIsInstance(ip, str)
        self.assertIsInstance(agent, str)
        self.assertIsInstance(info, dict)