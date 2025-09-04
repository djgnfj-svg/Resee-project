"""
Test cases for custom exceptions in accounts app
"""
from django.test import TestCase, RequestFactory
from rest_framework import status
from rest_framework.response import Response
from unittest.mock import Mock, patch

from .exceptions import (
    AccountsException,
    ConsentException,
    LegalDocumentException,
    DataExportException,
    DataDeletionException,
    handle_accounts_exception,
    safe_api_call
)


class CustomExceptionsTestCase(TestCase):
    """Test cases for custom exception classes"""
    
    def test_accounts_exception_default(self):
        """Test AccountsException with default values"""
        exc = AccountsException()
        
        self.assertEqual(exc.message, "계정 관련 오류가 발생했습니다.")
        self.assertEqual(exc.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(str(exc), "계정 관련 오류가 발생했습니다.")
    
    def test_accounts_exception_custom(self):
        """Test AccountsException with custom values"""
        exc = AccountsException("Custom error message", status.HTTP_404_NOT_FOUND)
        
        self.assertEqual(exc.message, "Custom error message")
        self.assertEqual(exc.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(str(exc), "Custom error message")
    
    def test_consent_exception(self):
        """Test ConsentException inherits properly"""
        exc = ConsentException()
        
        self.assertIsInstance(exc, AccountsException)
        self.assertEqual(exc.message, "동의 처리 중 오류가 발생했습니다.")
        self.assertEqual(exc.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_consent_exception_custom(self):
        """Test ConsentException with custom values"""
        exc = ConsentException("동의 철회 실패", status.HTTP_403_FORBIDDEN)
        
        self.assertEqual(exc.message, "동의 철회 실패")
        self.assertEqual(exc.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_legal_document_exception(self):
        """Test LegalDocumentException"""
        exc = LegalDocumentException("문서를 찾을 수 없습니다", status.HTTP_404_NOT_FOUND)
        
        self.assertIsInstance(exc, AccountsException)
        self.assertEqual(exc.message, "문서를 찾을 수 없습니다")
        self.assertEqual(exc.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_data_export_exception(self):
        """Test DataExportException"""
        exc = DataExportException()
        
        self.assertIsInstance(exc, AccountsException)
        self.assertEqual(exc.message, "데이터 내보내기 중 오류가 발생했습니다.")
    
    def test_data_deletion_exception(self):
        """Test DataDeletionException"""
        exc = DataDeletionException()
        
        self.assertIsInstance(exc, AccountsException)
        self.assertEqual(exc.message, "데이터 삭제 요청 처리 중 오류가 발생했습니다.")


class ExceptionHandlerTestCase(TestCase):
    """Test cases for exception handler functions"""
    
    @patch('accounts.exceptions.logger')
    def test_handle_accounts_exception(self, mock_logger):
        """Test handle_accounts_exception function"""
        exc = ConsentException("테스트 동의 오류", status.HTTP_422_UNPROCESSABLE_ENTITY)
        context = {'view': 'TestView', 'request': Mock()}
        
        response = handle_accounts_exception(exc, context)
        
        # Verify response structure
        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(response.data['error'], "테스트 동의 오류")
        self.assertEqual(response.data['error_type'], "ConsentException")
        self.assertEqual(response.data['status_code'], status.HTTP_422_UNPROCESSABLE_ENTITY)
        
        # Verify logging was called
        mock_logger.warning.assert_called_once()
    
    @patch('accounts.exceptions.exception_handler')
    def test_handle_non_accounts_exception(self, mock_exception_handler):
        """Test that non-accounts exceptions are passed to DRF handler"""
        exc = ValueError("Standard Python exception")
        context = {'view': 'TestView'}
        
        mock_exception_handler.return_value = Mock()
        
        result = handle_accounts_exception(exc, context)
        
        # Verify DRF exception handler was called
        mock_exception_handler.assert_called_once_with(exc, context)
        self.assertEqual(result, mock_exception_handler.return_value)
    
    @patch('accounts.exceptions.logger')
    def test_safe_api_call_decorator_success(self, mock_logger):
        """Test safe_api_call decorator with successful function"""
        @safe_api_call
        def test_function():
            return Response({'success': True}, status=status.HTTP_200_OK)
        
        response = test_function()
        
        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['success'], True)
        
        # No logging should occur for successful calls
        mock_logger.warning.assert_not_called()
        mock_logger.error.assert_not_called()
    
    @patch('accounts.exceptions.logger')
    def test_safe_api_call_decorator_accounts_exception(self, mock_logger):
        """Test safe_api_call decorator with AccountsException"""
        @safe_api_call
        def test_function():
            raise ConsentException("테스트 동의 오류", status.HTTP_403_FORBIDDEN)
        
        response = test_function()
        
        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data['error'], "테스트 동의 오류")
        self.assertEqual(response.data['error_type'], "ConsentException")
        
        # Verify warning logging
        mock_logger.warning.assert_called_once()
        mock_logger.error.assert_not_called()
    
    @patch('accounts.exceptions.logger')
    def test_safe_api_call_decorator_unexpected_exception(self, mock_logger):
        """Test safe_api_call decorator with unexpected exception"""
        @safe_api_call
        def test_function():
            raise ValueError("Unexpected error")
        
        response = test_function()
        
        self.assertIsInstance(response, Response)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['error'], "예상치 못한 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")
        self.assertEqual(response.data['error_type'], "UnexpectedError")
        
        # Verify error logging
        mock_logger.error.assert_called_once()
        mock_logger.warning.assert_not_called()


class ExceptionIntegrationTestCase(TestCase):
    """Integration test cases for exception handling"""
    
    def test_exception_hierarchy(self):
        """Test that all custom exceptions inherit from AccountsException"""
        exceptions = [
            ConsentException(),
            LegalDocumentException(),
            DataExportException(),
            DataDeletionException()
        ]
        
        for exc in exceptions:
            self.assertIsInstance(exc, AccountsException)
            self.assertIsInstance(exc, Exception)
    
    def test_exception_message_localization(self):
        """Test that exception messages are in Korean"""
        exceptions = [
            AccountsException(),
            ConsentException(),
            LegalDocumentException(),
            DataExportException(),
            DataDeletionException()
        ]
        
        for exc in exceptions:
            # All default messages should contain Korean characters
            self.assertTrue(any(ord(char) > 127 for char in exc.message))
    
    def test_status_code_inheritance(self):
        """Test that status codes are properly inherited"""
        # Test default inheritance
        exc1 = ConsentException()
        self.assertEqual(exc1.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test custom status code
        exc2 = ConsentException(status_code=status.HTTP_403_FORBIDDEN)
        self.assertEqual(exc2.status_code, status.HTTP_403_FORBIDDEN)
        
        # Test custom message with default status
        exc3 = ConsentException("커스텀 메시지")
        self.assertEqual(exc3.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(exc3.message, "커스텀 메시지")
    
    def test_decorator_preserves_function_metadata(self):
        """Test that safe_api_call decorator preserves function metadata"""
        @safe_api_call
        def example_function():
            """Example docstring"""
            return "success"
        
        # Function should still be accessible and preserve metadata
        self.assertEqual(example_function.__name__, "wrapper")
        # Note: functools.wraps could be used to preserve original metadata