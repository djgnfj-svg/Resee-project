"""
Custom exceptions and error handlers for accounts app
"""
import logging
from typing import Dict, Any, Optional
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


logger = logging.getLogger(__name__)


class AccountsException(Exception):
    """Base exception class for accounts app"""
    default_message = "계정 관련 오류가 발생했습니다."
    default_status_code = status.HTTP_400_BAD_REQUEST
    
    def __init__(self, message: Optional[str] = None, status_code: Optional[int] = None):
        self.message = message or self.default_message
        self.status_code = status_code or self.default_status_code
        super().__init__(self.message)


class ConsentException(AccountsException):
    """동의 관련 예외"""
    default_message = "동의 처리 중 오류가 발생했습니다."


class LegalDocumentException(AccountsException):
    """법적 문서 관련 예외"""
    default_message = "법적 문서 처리 중 오류가 발생했습니다."


class DataExportException(AccountsException):
    """데이터 내보내기 관련 예외"""
    default_message = "데이터 내보내기 중 오류가 발생했습니다."


class DataDeletionException(AccountsException):
    """데이터 삭제 관련 예외"""
    default_message = "데이터 삭제 요청 처리 중 오류가 발생했습니다."


def handle_accounts_exception(exc: Exception, context: Dict[str, Any]) -> Response:
    """
    Handle accounts app exceptions with standardized error responses
    
    Args:
        exc: The exception that was raised
        context: Additional context information
        
    Returns:
        Response: Standardized error response
    """
    if isinstance(exc, AccountsException):
        logger.warning(f"Accounts exception: {exc.message}", extra={
            'exception_type': type(exc).__name__,
            'status_code': exc.status_code,
            'context': context
        })
        
        return Response({
            'error': exc.message,
            'error_type': type(exc).__name__,
            'status_code': exc.status_code
        }, status=exc.status_code)
    
    # Let DRF handle other exceptions
    return exception_handler(exc, context)


def safe_api_call(func):
    """
    Decorator for safe API calls with standardized exception handling
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except AccountsException as e:
            logger.warning(f"Accounts API exception: {e.message}")
            return Response({
                'error': e.message,
                'error_type': type(e).__name__
            }, status=e.status_code)
        except Exception as e:
            logger.error(f"Unexpected API exception: {str(e)}")
            return Response({
                'error': '예상치 못한 오류가 발생했습니다. 잠시 후 다시 시도해주세요.',
                'error_type': 'UnexpectedError'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return wrapper