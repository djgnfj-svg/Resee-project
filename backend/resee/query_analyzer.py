"""
Database query performance analysis tools
"""
import json
import logging
import time
from collections import Counter, defaultdict
from functools import wraps

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection, reset_queries

logger = logging.getLogger('performance')


class QueryAnalyzer:
    """
    Tool for analyzing database query performance
    """
    
    def __init__(self):
        self.query_stats = defaultdict(list)
        self.slow_queries = []
        self.duplicate_queries = Counter()
        
    def analyze_queries(self, queries):
        """
        Analyze a list of Django queries for performance issues
        """
        for query in queries:
            query_time = float(query['time'])
            sql = query['sql']
            
            # Track slow queries (>100ms)
            if query_time > 0.1:
                self.slow_queries.append({
                    'sql': sql,
                    'time': query_time,
                    'explanation': self._explain_slow_query(sql)
                })
            
            # Track duplicate queries
            normalized_sql = self._normalize_sql(sql)
            self.duplicate_queries[normalized_sql] += 1
            
            # Categorize queries
            query_type = self._categorize_query(sql)
            self.query_stats[query_type].append(query_time)
    
    def _normalize_sql(self, sql):
        """
        Normalize SQL to detect duplicate queries with different parameters
        """
        # Replace parameter placeholders
        import re
        normalized = re.sub(r"'[^']*'", "'?'", sql)
        normalized = re.sub(r'\b\d+\b', '?', normalized)
        return normalized
    
    def _categorize_query(self, sql):
        """
        Categorize query by type (SELECT, INSERT, UPDATE, DELETE)
        """
        sql_upper = sql.upper().strip()
        if sql_upper.startswith('SELECT'):
            return 'SELECT'
        elif sql_upper.startswith('INSERT'):
            return 'INSERT'
        elif sql_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif sql_upper.startswith('DELETE'):
            return 'DELETE'
        else:
            return 'OTHER'
    
    def _explain_slow_query(self, sql):
        """
        Provide explanation for why a query might be slow
        """
        explanations = []
        
        if 'JOIN' not in sql.upper() and 'WHERE' in sql.upper():
            explanations.append("Missing indexes on WHERE clause columns")
        
        if sql.upper().count('JOIN') > 3:
            explanations.append("Complex query with multiple JOINs")
        
        if 'ORDER BY' in sql.upper() and 'LIMIT' not in sql.upper():
            explanations.append("ORDER BY without LIMIT can be expensive")
        
        if 'COUNT(*)' in sql.upper():
            explanations.append("COUNT(*) on large tables is expensive")
        
        return explanations
    
    def get_report(self):
        """
        Generate a performance analysis report
        """
        report = {
            'summary': {
                'total_queries': sum(len(queries) for queries in self.query_stats.values()),
                'slow_queries_count': len(self.slow_queries),
                'duplicate_queries_count': sum(1 for count in self.duplicate_queries.values() if count > 1),
                'query_types': {qtype: len(queries) for qtype, queries in self.query_stats.items()}
            },
            'slow_queries': self.slow_queries[:10],  # Top 10 slowest
            'duplicate_queries': [
                {'sql': sql, 'count': count} 
                for sql, count in self.duplicate_queries.most_common(10) 
                if count > 1
            ],
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_recommendations(self):
        """
        Generate performance optimization recommendations
        """
        recommendations = []
        
        if len(self.slow_queries) > 0:
            recommendations.append("Consider adding database indexes for slow queries")
        
        if any(count > 5 for count in self.duplicate_queries.values()):
            recommendations.append("Use select_related() and prefetch_related() to reduce duplicate queries")
        
        select_queries = self.query_stats.get('SELECT', [])
        if len(select_queries) > 20:
            recommendations.append("Consider implementing pagination for large data sets")
        
        if any(time > 0.5 for time in select_queries):
            recommendations.append("Review database schema and add missing indexes")
        
        return recommendations


def query_performance_analyzer(func):
    """
    Decorator to analyze query performance for a specific function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not settings.DEBUG:
            return func(*args, **kwargs)
        
        # Reset query count
        reset_queries()
        start_time = time.time()
        
        # Execute function
        result = func(*args, **kwargs)
        
        # Analyze performance
        end_time = time.time()
        execution_time = end_time - start_time
        
        analyzer = QueryAnalyzer()
        analyzer.analyze_queries(connection.queries)
        report = analyzer.get_report()
        
        # Log performance metrics
        logger.info(f"Function: {func.__name__}", extra={
            'execution_time': execution_time,
            'query_count': report['summary']['total_queries'],
            'slow_queries': report['summary']['slow_queries_count'],
            'duplicate_queries': report['summary']['duplicate_queries_count'],
            'recommendations': report['recommendations']
        })
        
        # Warn about performance issues
        if report['summary']['slow_queries_count'] > 0:
            logger.warning(f"Function {func.__name__} has {report['summary']['slow_queries_count']} slow queries")
        
        if report['summary']['duplicate_queries_count'] > 5:
            logger.warning(f"Function {func.__name__} has {report['summary']['duplicate_queries_count']} duplicate queries (N+1 problem?)")
        
        return result
    
    return wrapper


class DatabaseAnalyzerMiddleware:
    """
    Middleware to analyze database queries for each request
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        if not settings.DEBUG:
            return self.get_response(request)
        
        # Reset query count
        reset_queries()
        start_time = time.time()
        
        # Process request
        response = self.get_response(request)
        
        # Analyze performance
        end_time = time.time()
        execution_time = end_time - start_time
        
        analyzer = QueryAnalyzer()
        analyzer.analyze_queries(connection.queries)
        report = analyzer.get_report()
        
        # Add performance headers for development
        response['X-Query-Count'] = str(report['summary']['total_queries'])
        response['X-Query-Time'] = f"{execution_time:.3f}s"
        response['X-Slow-Queries'] = str(report['summary']['slow_queries_count'])
        
        # Log performance issues
        if report['summary']['total_queries'] > 20:
            logger.warning(f"High query count for {request.path}: {report['summary']['total_queries']} queries")
        
        if execution_time > 1.0:
            logger.warning(f"Slow request {request.path}: {execution_time:.3f}s")
        
        return response


class QueryOptimizationSuggestions:
    """
    Generate specific optimization suggestions based on query patterns
    """
    
    @staticmethod
    def analyze_model_queries(model_class):
        """
        Analyze common query patterns for a specific model
        """
        model_name = model_class.__name__
        table_name = model_class._meta.db_table
        
        suggestions = []
        
        # Check for missing select_related opportunities
        foreign_keys = [
            field.name for field in model_class._meta.fields 
            if field.get_internal_type() == 'ForeignKey'
        ]
        
        if foreign_keys:
            suggestions.append({
                'type': 'select_related',
                'description': f"Use select_related({', '.join(foreign_keys)}) for {model_name} queries",
                'impact': 'Reduces database round trips for foreign key lookups'
            })
        
        # Check for missing prefetch_related opportunities
        many_to_many = [
            field.name for field in model_class._meta.many_to_many
        ]
        reverse_relations = [
            rel.get_accessor_name() for rel in model_class._meta.related_objects
            if rel.one_to_many or rel.one_to_one
        ]
        
        prefetch_candidates = many_to_many + reverse_relations
        if prefetch_candidates:
            suggestions.append({
                'type': 'prefetch_related',
                'description': f"Use prefetch_related({', '.join(prefetch_candidates)}) for {model_name} queries",
                'impact': 'Reduces N+1 queries for related objects'
            })
        
        # Check for indexing opportunities
        indexed_fields = ['created_at', 'updated_at', 'is_active', 'status']
        model_fields = [field.name for field in model_class._meta.fields]
        
        missing_indexes = [
            field for field in indexed_fields 
            if field in model_fields
        ]
        
        if missing_indexes:
            suggestions.append({
                'type': 'database_index',
                'description': f"Consider adding indexes for {model_name} fields: {', '.join(missing_indexes)}",
                'impact': 'Improves query performance for filtering and ordering'
            })
        
        return suggestions
    
    @staticmethod
    def get_all_model_suggestions():
        """
        Get optimization suggestions for all models in the project
        """
        from django.apps import apps
        
        all_suggestions = {}
        
        for model in apps.get_models():
            suggestions = QueryOptimizationSuggestions.analyze_model_queries(model)
            if suggestions:
                all_suggestions[model.__name__] = suggestions
        
        return all_suggestions


# Utility functions for performance testing
def measure_query_performance(func, iterations=100):
    """
    Measure query performance over multiple iterations
    """
    times = []
    query_counts = []
    
    for _ in range(iterations):
        reset_queries()
        start_time = time.time()
        
        func()
        
        end_time = time.time()
        times.append(end_time - start_time)
        query_counts.append(len(connection.queries))
    
    return {
        'avg_time': sum(times) / len(times),
        'min_time': min(times),
        'max_time': max(times),
        'avg_queries': sum(query_counts) / len(query_counts),
        'total_iterations': iterations
    }


def profile_database_operations():
    """
    Profile common database operations to identify bottlenecks
    """
    from django.contrib.auth import get_user_model

    from content.models import Category, Content
    from review.models import ReviewSchedule
    
    User = get_user_model()
    
    # Create test data if needed
    user, _ = User.objects.get_or_create(
        email='performance_test@example.com',
        defaults={'password': 'testpass123'}
    )
    
    profiles = {}
    
    # Profile content listing
    def list_contents():
        list(Content.objects.filter(author=user)[:20])
    
    profiles['content_list'] = measure_query_performance(list_contents)
    
    # Profile content with categories
    def list_contents_with_categories():
        list(Content.objects.filter(author=user).select_related('category')[:20])
    
    profiles['content_list_optimized'] = measure_query_performance(list_contents_with_categories)
    
    # Profile review schedules
    def list_review_schedules():
        list(ReviewSchedule.objects.filter(user=user)[:20])
    
    profiles['review_schedules'] = measure_query_performance(list_review_schedules)
    
    return profiles