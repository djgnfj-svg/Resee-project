"""
Performance optimization utilities
"""
import time
import logging
from functools import wraps
from django.db import connection
from django.conf import settings

logger = logging.getLogger(__name__)


def query_debugger(func):
    """
    Decorator to log database queries for performance analysis
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not settings.DEBUG:
            return func(*args, **kwargs)
        
        initial_queries = len(connection.queries)
        start_time = time.time()
        
        result = func(*args, **kwargs)
        
        end_time = time.time()
        execution_time = end_time - start_time
        num_queries = len(connection.queries) - initial_queries
        
        if num_queries > 10 or execution_time > 1.0:
            logger.warning(
                f"Performance issue in {func.__name__}: "
                f"{num_queries} queries, {execution_time:.2f}s"
            )
            
            # Log slow queries
            for query in connection.queries[initial_queries:]:
                query_time = float(query['time'])
                if query_time > 0.1:  # Log queries slower than 100ms
                    logger.warning(f"Slow query ({query_time}s): {query['sql'][:200]}...")
        
        return result
    return wrapper


def optimize_queryset(queryset, select_related=None, prefetch_related=None):
    """
    Helper to optimize querysets with common patterns
    """
    if select_related:
        queryset = queryset.select_related(*select_related)
    
    if prefetch_related:
        queryset = queryset.prefetch_related(*prefetch_related)
    
    return queryset


class PerformanceMonitor:
    """
    Context manager for monitoring performance
    """
    
    def __init__(self, operation_name):
        self.operation_name = operation_name
        self.start_time = None
        self.initial_queries = None
    
    def __enter__(self):
        self.start_time = time.time()
        if settings.DEBUG:
            self.initial_queries = len(connection.queries)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = time.time() - self.start_time
        
        if settings.DEBUG and self.initial_queries is not None:
            num_queries = len(connection.queries) - self.initial_queries
            
            logger.info(
                f"Performance: {self.operation_name} - "
                f"{execution_time:.2f}s, {num_queries} queries"
            )
        
        # Log performance issues
        if execution_time > 2.0:
            logger.warning(
                f"Slow operation: {self.operation_name} took {execution_time:.2f}s"
            )


def bulk_create_with_batch_size(model_class, objects, batch_size=1000):
    """
    Bulk create objects with optimal batch size
    """
    created_objects = []
    for i in range(0, len(objects), batch_size):
        batch = objects[i:i + batch_size]
        created_objects.extend(
            model_class.objects.bulk_create(batch, ignore_conflicts=False)
        )
    return created_objects


def get_or_create_bulk(model_class, objects_data, batch_size=1000):
    """
    Optimized bulk get_or_create operation
    """
    created = []
    updated = []
    
    for i in range(0, len(objects_data), batch_size):
        batch = objects_data[i:i + batch_size]
        
        for data in batch:
            obj, was_created = model_class.objects.get_or_create(**data)
            if was_created:
                created.append(obj)
            else:
                updated.append(obj)
    
    return created, updated