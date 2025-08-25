"""
Performance monitoring utilities for the Resee application
"""
import time
import logging
from functools import wraps
from django.db import connection
from django.conf import settings

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Performance monitoring utility class"""
    
    @staticmethod
    def log_execution_time(func_name, execution_time):
        """Log function execution time"""
        if settings.DEBUG:
            logger.info(f"Performance: {func_name} took {execution_time:.2f}ms")
    
    @staticmethod
    def log_query_count(func_name, query_count):
        """Log database query count"""
        if settings.DEBUG:
            logger.info(f"Performance: {func_name} executed {query_count} queries")


def performance_monitor(func):
    """
    Decorator to monitor function performance
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not settings.DEBUG:
            return func(*args, **kwargs)
        
        start_time = time.time()
        start_queries = len(connection.queries)
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        end_queries = len(connection.queries)
        
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        query_count = end_queries - start_queries
        
        PerformanceMonitor.log_execution_time(func.__name__, execution_time)
        PerformanceMonitor.log_query_count(func.__name__, query_count)
        
        return result
    return wrapper


def query_debugger(func):
    """
    Decorator to debug database queries
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not settings.DEBUG:
            return func(*args, **kwargs)
        
        start_queries = len(connection.queries)
        
        result = func(*args, **kwargs)
        
        end_queries = len(connection.queries)
        new_queries = connection.queries[start_queries:end_queries]
        
        if new_queries:
            logger.debug(f"Queries executed in {func.__name__}:")
            for i, query in enumerate(new_queries, 1):
                logger.debug(f"  {i}. {query['sql'][:200]}...")
                logger.debug(f"     Time: {query['time']}s")
        
        return result
    return wrapper


class DatabaseQueryTracker:
    """Context manager for tracking database queries"""
    
    def __init__(self, description=""):
        self.description = description
        self.start_queries = 0
        self.end_queries = 0
    
    def __enter__(self):
        self.start_queries = len(connection.queries)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_queries = len(connection.queries)
        query_count = self.end_queries - self.start_queries
        
        if settings.DEBUG:
            desc = self.description or "Block"
            logger.info(f"Database queries in {desc}: {query_count}")


def measure_time(func):
    """
    Simple decorator to measure execution time
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        
        if settings.DEBUG:
            logger.debug(f"{func.__name__} executed in {(end-start)*1000:.2f}ms")
        
        return result
    return wrapper