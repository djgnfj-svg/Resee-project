"""
Custom pagination classes for optimized performance
"""
import logging

from django.conf import settings
from django.core.paginator import Paginator
from django.db import connection
from rest_framework.pagination import (LimitOffsetPagination,
                                       PageNumberPagination)
from rest_framework.response import Response

logger = logging.getLogger(__name__)


class OptimizedPageNumberPagination(PageNumberPagination):
    """
    Optimized pagination with performance metrics and count optimization
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        # Add performance metrics in debug mode
        response_data = {
            'links': {
                'next': self.get_next_link(),
                'previous': self.get_previous_link()
            },
            'count': self.page.paginator.count,
            'page_size': self.page_size,
            'current_page': self.page.number,
            'total_pages': self.page.paginator.num_pages,
            'results': data
        }
        
        # Add debug info in development
        if settings.DEBUG:
            response_data['debug'] = {
                'query_count': len(connection.queries) if hasattr(connection, 'queries') else 0,
                'page_info': {
                    'has_next': self.page.has_next(),
                    'has_previous': self.page.has_previous(),
                    'start_index': self.page.start_index(),
                    'end_index': self.page.end_index(),
                }
            }
        
        return Response(response_data)


class FastCountPagination(PageNumberPagination):
    """
    Pagination that uses estimated count for better performance on large datasets
    """
    page_size = 20
    page_size_query_param = 'page_size'  
    max_page_size = 100
    
    def paginate_queryset(self, queryset, request, view=None):
        """
        Override to use estimated count for large tables
        """
        # For small datasets, use regular pagination
        if hasattr(queryset.model._meta, 'db_table'):
            table_name = queryset.model._meta.db_table
            
            # Estimate table size (this is PostgreSQL specific)
            with connection.cursor() as cursor:
                try:
                    cursor.execute(
                        "SELECT reltuples::BIGINT AS estimate FROM pg_class WHERE relname = %s",
                        [table_name]
                    )
                    result = cursor.fetchone()
                    estimated_count = result[0] if result else 0
                    
                    # If table is large (>10000 rows), use estimation
                    if estimated_count > 10000:
                        logger.info(f"Using estimated count for {table_name}: {estimated_count}")
                        # Use custom paginator that doesn't count all rows
                        return self._paginate_with_estimation(queryset, request, estimated_count)
                        
                except Exception as e:
                    logger.warning(f"Failed to get estimated count for {table_name}: {e}")
        
        # Fall back to regular pagination for small datasets
        return super().paginate_queryset(queryset, request, view)
    
    def _paginate_with_estimation(self, queryset, request, estimated_count):
        """
        Custom pagination logic that avoids full count queries
        """
        page_size = self.get_page_size(request)
        if not page_size:
            return None
            
        paginator = EstimatedCountPaginator(queryset, page_size, estimated_count)
        page_number = request.GET.get(self.page_query_param, 1)
        
        try:
            self.page = paginator.page(page_number)
            return list(self.page)
        except Exception as e:
            logger.error(f"Pagination error: {e}")
            return None


class EstimatedCountPaginator(Paginator):
    """
    Custom paginator that uses estimated count to avoid expensive COUNT queries
    """
    def __init__(self, object_list, per_page, estimated_count, orphans=0, allow_empty_first_page=True):
        super().__init__(object_list, per_page, orphans, allow_empty_first_page)
        self._estimated_count = estimated_count
        
    @property
    def count(self):
        """Return estimated count instead of actual count"""
        return self._estimated_count
    
    @property  
    def num_pages(self):
        """Calculate number of pages based on estimated count"""
        if self._estimated_count == 0:
            return 1
        return (self._estimated_count - 1) // self.per_page + 1


class AnalyticsPagination(OptimizedPageNumberPagination):
    """
    Specialized pagination for analytics data with additional metadata
    """
    page_size = 50  # Analytics usually need more data per page
    max_page_size = 500
    
    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        
        # Add analytics-specific metadata
        if hasattr(self.page, 'object_list') and self.page.object_list:
            response.data['analytics_meta'] = {
                'date_range': self._get_date_range(self.page.object_list),
                'data_points': len(data),
                'aggregation_level': getattr(self, 'aggregation_level', 'day')
            }
        
        return response
    
    def _get_date_range(self, object_list):
        """Extract date range from analytics data"""
        try:
            dates = []
            for obj in object_list:
                if hasattr(obj, 'created_at'):
                    dates.append(obj.created_at.date())
                elif hasattr(obj, 'date'):
                    dates.append(obj.date)
            
            if dates:
                return {
                    'start_date': min(dates).isoformat(),
                    'end_date': max(dates).isoformat()
                }
        except Exception as e:
            logger.warning(f"Failed to calculate date range: {e}")
        
        return None


class ContentPagination(OptimizedPageNumberPagination):
    """
    Specialized pagination for content with category information
    """
    page_size = 15  # Content pages usually show fewer items
    
    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        
        # Add content-specific metadata
        if data:
            categories = set()
            priorities = {'high': 0, 'medium': 0, 'low': 0}
            
            for item in data:
                if 'category' in item and item['category']:
                    # Handle both dict (nested serializer) and int (just ID) cases
                    if isinstance(item['category'], dict):
                        categories.add(item['category'].get('name', 'Unknown'))
                    else:
                        categories.add(f'Category {item["category"]}')
                if 'priority' in item:
                    priorities[item['priority']] = priorities.get(item['priority'], 0) + 1
            
            response.data['content_meta'] = {
                'categories_in_page': list(categories),
                'priority_distribution': priorities
            }
        
        return response


class ReviewPagination(OptimizedPageNumberPagination):
    """
    Specialized pagination for review data with performance stats
    """
    page_size = 25
    
    def get_paginated_response(self, data):
        response = super().get_paginated_response(data)
        
        # Add review-specific statistics
        if data:
            total_reviews = len(data)
            completed_reviews = sum(1 for item in data if item.get('completed', False))
            
            response.data['review_meta'] = {
                'completion_rate': round(completed_reviews / total_reviews * 100, 1) if total_reviews > 0 else 0,
                'total_reviews_in_page': total_reviews,
                'completed_reviews_in_page': completed_reviews
            }
        
        return response


# Pagination class mapping for easy configuration
PAGINATION_CLASSES = {
    'default': OptimizedPageNumberPagination,
    'fast_count': FastCountPagination,
    'analytics': AnalyticsPagination,
    'content': ContentPagination,
    'review': ReviewPagination,
}


def get_pagination_class(pagination_type='default'):
    """
    Factory function to get pagination class by type
    """
    return PAGINATION_CLASSES.get(pagination_type, OptimizedPageNumberPagination)