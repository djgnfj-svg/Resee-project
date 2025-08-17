"""
Structured logging system for comprehensive monitoring and debugging
"""
import json
import logging
import time
import traceback
import uuid
from contextlib import contextmanager
from functools import wraps
from typing import Any, Dict, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs structured JSON logs
    """
    
    def format(self, record):
        log_entry = {
            'timestamp': timezone.now().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'thread_id': record.thread,
            'process_id': record.process,
        }
        
        # Add exception information if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': self.formatException(record.exc_info)
            }
        
        # Add extra fields from the record
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'lineno', 'funcName', 'created', 
                          'msecs', 'relativeCreated', 'thread', 'threadName', 
                          'processName', 'process', 'exc_info', 'exc_text', 'stack_info']:
                log_entry['extra'] = getattr(log_entry, 'extra', {})
                log_entry['extra'][key] = value
        
        return json.dumps(log_entry, ensure_ascii=False)


class APILogger:
    """
    Specialized logger for API requests and responses
    """
    
    def __init__(self):
        self.logger = logging.getLogger('api')
    
    def log_request(self, request, **extra):
        """Log incoming API request"""
        user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
        
        log_data = {
            'event_type': 'api_request',
            'method': request.method,
            'path': request.path,
            'user_id': user_id,
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': self._get_client_ip(request),
            'query_params': dict(request.GET),
            'request_id': str(uuid.uuid4()),
            **extra
        }
        
        # Don't log sensitive data in body
        if request.method in ['POST', 'PUT', 'PATCH']:
            content_type = request.META.get('CONTENT_TYPE', '')
            if 'application/json' in content_type and hasattr(request, 'data'):
                # Filter out sensitive fields
                filtered_data = self._filter_sensitive_data(dict(request.data))
                log_data['request_body'] = filtered_data
        
        self.logger.info("API request received", extra=log_data)
        return log_data['request_id']
    
    def log_response(self, request_id, status_code, response_time_ms, **extra):
        """Log API response"""
        log_data = {
            'event_type': 'api_response',
            'request_id': request_id,
            'status_code': status_code,
            'response_time_ms': response_time_ms,
            **extra
        }
        
        level = logging.INFO
        if status_code >= 400:
            level = logging.ERROR if status_code >= 500 else logging.WARNING
        
        self.logger.log(level, f"API response {status_code}", extra=log_data)
    
    def log_error(self, request, exception, **extra):
        """Log API errors"""
        user_id = getattr(request.user, 'id', None) if hasattr(request, 'user') else None
        
        log_data = {
            'event_type': 'api_error',
            'method': request.method,
            'path': request.path,
            'user_id': user_id,
            'error_type': type(exception).__name__,
            'error_message': str(exception),
            'traceback': traceback.format_exc(),
            **extra
        }
        
        self.logger.error("API error occurred", extra=log_data)
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def _filter_sensitive_data(self, data):
        """Remove sensitive information from log data"""
        sensitive_fields = ['password', 'token', 'secret', 'key', 'authorization']
        
        if isinstance(data, dict):
            filtered = {}
            for key, value in data.items():
                if any(sensitive in key.lower() for sensitive in sensitive_fields):
                    filtered[key] = '[FILTERED]'
                elif isinstance(value, dict):
                    filtered[key] = self._filter_sensitive_data(value)
                else:
                    filtered[key] = value
            return filtered
        return data


class PerformanceLogger:
    """
    Logger for performance metrics and database queries
    """
    
    def __init__(self):
        self.logger = logging.getLogger('performance')
    
    def log_query_performance(self, query_count, execution_time, endpoint, **extra):
        """Log database query performance"""
        log_data = {
            'event_type': 'query_performance',
            'query_count': query_count,
            'execution_time_ms': execution_time * 1000,
            'endpoint': endpoint,
            'queries_per_second': query_count / execution_time if execution_time > 0 else 0,
            **extra
        }
        
        level = logging.INFO
        if query_count > 20:
            level = logging.WARNING
        if query_count > 50:
            level = logging.ERROR
        
        self.logger.log(level, f"Query performance: {query_count} queries", extra=log_data)
    
    def log_slow_operation(self, operation_name, execution_time, **extra):
        """Log slow operations"""
        log_data = {
            'event_type': 'slow_operation',
            'operation': operation_name,
            'execution_time_ms': execution_time * 1000,
            **extra
        }
        
        self.logger.warning(f"Slow operation detected: {operation_name}", extra=log_data)
    
    def log_cache_performance(self, cache_key, hit, execution_time=None, **extra):
        """Log cache hit/miss performance"""
        log_data = {
            'event_type': 'cache_performance',
            'cache_key': cache_key,
            'cache_hit': hit,
            'execution_time_ms': execution_time * 1000 if execution_time else None,
            **extra
        }
        
        self.logger.info(f"Cache {'hit' if hit else 'miss'}: {cache_key}", extra=log_data)


class SecurityLogger:
    """
    Logger for security-related events
    """
    
    def __init__(self):
        self.logger = logging.getLogger('security')
    
    def log_authentication_attempt(self, email, success, ip_address, **extra):
        """Log authentication attempts"""
        log_data = {
            'event_type': 'authentication_attempt',
            'email': email,
            'success': success,
            'ip_address': ip_address,
            **extra
        }
        
        level = logging.INFO if success else logging.WARNING
        message = f"Authentication {'successful' if success else 'failed'} for {email}"
        self.logger.log(level, message, extra=log_data)
    
    def log_authorization_failure(self, user_id, resource, action, **extra):
        """Log authorization failures"""
        log_data = {
            'event_type': 'authorization_failure',
            'user_id': user_id,
            'resource': resource,
            'action': action,
            **extra
        }
        
        self.logger.warning(f"Authorization denied for user {user_id}", extra=log_data)
    
    def log_suspicious_activity(self, user_id, activity_type, details, **extra):
        """Log suspicious activities"""
        log_data = {
            'event_type': 'suspicious_activity',
            'user_id': user_id,
            'activity_type': activity_type,
            'details': details,
            **extra
        }
        
        self.logger.error(f"Suspicious activity detected: {activity_type}", extra=log_data)


class AILogger:
    """
    Specialized logger for AI operations
    """
    
    def __init__(self):
        self.logger = logging.getLogger('ai')
    
    def log_question_generation(self, user_id, content_id, question_types, count, success, **extra):
        """Log AI question generation"""
        log_data = {
            'event_type': 'ai_question_generation',
            'user_id': user_id,
            'content_id': content_id,
            'question_types': question_types,
            'requested_count': count,
            'success': success,
            **extra
        }
        
        level = logging.INFO if success else logging.ERROR
        message = f"AI question generation {'successful' if success else 'failed'}"
        self.logger.log(level, message, extra=log_data)
    
    def log_api_usage(self, api_provider, model, tokens_used, cost_usd, **extra):
        """Log AI API usage and costs"""
        log_data = {
            'event_type': 'ai_api_usage',
            'api_provider': api_provider,
            'model': model,
            'tokens_used': tokens_used,
            'cost_usd': cost_usd,
            **extra
        }
        
        self.logger.info(f"AI API usage: {tokens_used} tokens, ${cost_usd}", extra=log_data)
    
    def log_quality_evaluation(self, question_id, quality_score, auto_approved, **extra):
        """Log AI question quality evaluation"""
        log_data = {
            'event_type': 'ai_quality_evaluation',
            'question_id': question_id,
            'quality_score': quality_score,
            'auto_approved': auto_approved,
            **extra
        }
        
        level = logging.INFO if auto_approved else logging.WARNING
        self.logger.log(level, f"Question quality evaluation: {quality_score}", extra=log_data)


# Logger instances
api_logger = APILogger()
performance_logger = PerformanceLogger()
security_logger = SecurityLogger()
ai_logger = AILogger()


# Decorators for automatic logging
def log_api_call(func):
    """Decorator to automatically log API calls"""
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        start_time = time.time()
        request_id = api_logger.log_request(request)
        
        try:
            response = func(self, request, *args, **kwargs)
            
            # Log successful response
            execution_time = (time.time() - start_time) * 1000
            status_code = getattr(response, 'status_code', 200)
            api_logger.log_response(request_id, status_code, execution_time)
            
            return response
            
        except Exception as e:
            # Log error
            api_logger.log_error(request, e)
            raise
    
    return wrapper


def log_performance(operation_name=None):
    """Decorator to log performance metrics"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                
                # Log performance metrics
                if execution_time > 1.0:  # Log slow operations (>1s)
                    performance_logger.log_slow_operation(op_name, execution_time)
                
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                performance_logger.log_slow_operation(
                    op_name, execution_time, 
                    error=str(e), error_type=type(e).__name__
                )
                raise
        
        return wrapper
    return decorator


@contextmanager
def log_context(logger_name, event_type, **context_data):
    """Context manager for logging operations with entry/exit"""
    logger = logging.getLogger(logger_name)
    start_time = time.time()
    
    # Log entry
    logger.info(f"Starting {event_type}", extra={
        'event_type': f'{event_type}_start',
        **context_data
    })
    
    try:
        yield
        
        # Log successful completion
        execution_time = (time.time() - start_time) * 1000
        logger.info(f"Completed {event_type}", extra={
            'event_type': f'{event_type}_complete',
            'execution_time_ms': execution_time,
            **context_data
        })
        
    except Exception as e:
        # Log error
        execution_time = (time.time() - start_time) * 1000
        logger.error(f"Failed {event_type}", extra={
            'event_type': f'{event_type}_error',
            'execution_time_ms': execution_time,
            'error_type': type(e).__name__,
            'error_message': str(e),
            **context_data
        })
        raise


# Middleware for automatic request logging
class StructuredLoggingMiddleware:
    """
    Middleware to automatically log all requests with structured data
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start_time = time.time()
        request_id = api_logger.log_request(request)
        
        # Add request ID to request for correlation
        request.log_request_id = request_id
        
        try:
            response = self.get_response(request)
            
            # Log response
            execution_time = (time.time() - start_time) * 1000
            api_logger.log_response(request_id, response.status_code, execution_time)
            
            # Add request ID to response headers for debugging
            response['X-Request-ID'] = request_id
            
            return response
            
        except Exception as e:
            api_logger.log_error(request, e)
            raise
    
    def process_exception(self, request, exception):
        """Handle exceptions that occur during request processing"""
        api_logger.log_error(request, exception)
        return None