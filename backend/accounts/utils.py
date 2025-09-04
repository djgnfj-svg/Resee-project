"""
Utility functions for accounts app
"""
from typing import Dict
from django.http import HttpRequest


def get_client_ip(request: HttpRequest) -> str:
    """
    Extract client IP address from request headers
    
    Args:
        request: Django HTTP request object
        
    Returns:
        str: Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '')
    return ip


def get_user_agent(request: HttpRequest) -> str:
    """
    Extract user agent from request headers
    
    Args:
        request: Django HTTP request object
        
    Returns:
        str: User agent string
    """
    return request.META.get('HTTP_USER_AGENT', '')


def collect_client_info(request: HttpRequest) -> Dict[str, str]:
    """
    Collect client information (IP and User Agent) from request
    
    Args:
        request: Django HTTP request object
        
    Returns:
        dict: Dictionary containing 'ip_address' and 'user_agent'
    """
    return {
        'ip_address': get_client_ip(request),
        'user_agent': get_user_agent(request)
    }