import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.http import JsonResponse

User = get_user_model()
logger = logging.getLogger(__name__)


class EmailVerificationMiddleware:
    """
    Middleware to ensure users have verified their email before accessing protected resources.
    Only applies to authenticated users who haven't verified their email.
    """
    
    # URLs that don't require email verification
    ALLOWED_PATHS = [
        '/api/accounts/verify-email/',
        '/api/accounts/resend-verification/',
        '/api/accounts/profile/',  # Allow profile access for account info
        '/api/auth/token/refresh/',  # Allow token refresh
        '/api/auth/token/',  # Allow login attempts (handled by serializer)
        '/admin/',  # Allow admin access
        '/api/docs/',  # Allow API docs
        '/api/swagger/',
        '/api/redoc/',
    ]
    
    # URL prefixes that don't require email verification
    ALLOWED_PREFIXES = [
        '/static/',
        '/media/',
        '/api/accounts/users/register/',  # Allow registration
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Process the request
        response = self.process_request(request)
        if response:
            return response
            
        # Continue to the view
        response = self.get_response(request)
        return response
    
    def process_request(self, request):
        """Check if the user needs email verification before accessing the resource."""
        
        # Skip verification check in DEBUG mode or if email verification is disabled
        if settings.DEBUG and not getattr(settings, 'ENFORCE_EMAIL_VERIFICATION', False):
            return None
            
        # Skip if user is not authenticated
        if not request.user.is_authenticated:
            return None
            
        # Skip if user is superuser (admin)
        if request.user.is_superuser:
            return None
            
        # Skip if user has already verified their email
        if getattr(request.user, 'is_email_verified', True):
            return None
            
        # Skip if path is in allowed paths
        path = request.path
        if any(path.startswith(prefix) for prefix in self.ALLOWED_PREFIXES):
            return None
            
        if path in self.ALLOWED_PATHS:
            return None
            
        # Skip for specific HTTP methods (like OPTIONS for CORS)
        if request.method in ['OPTIONS', 'HEAD']:
            return None
            
        # Log the blocked request
        logger.info(f"Blocked unverified user {request.user.email} from accessing {path}")
        
        # Return error response for API requests
        if path.startswith('/api/'):
            return JsonResponse({
                'error': '이메일 인증이 필요합니다.',
                'detail': '계정 보안을 위해 이메일 인증을 완료해주세요.',
                'requires_email_verification': True,
                'user_email': request.user.email
            }, status=403)
            
        # For non-API requests, we could redirect to a verification page
        # but since this is primarily an API backend, we'll return JSON
        return JsonResponse({
            'error': '이메일 인증이 필요합니다.',
            'detail': '계정 보안을 위해 이메일 인증을 완료해주세요.',
            'requires_email_verification': True
        }, status=403)