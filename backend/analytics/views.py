from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from review.models import ReviewHistory
from review.utils import calculate_success_rate, get_today_reviews_count, get_pending_reviews_count


class DashboardView(APIView):
    """Dashboard analytics view"""
    
    def get(self, request):
        """Get dashboard data - optimized version"""
        user = request.user
        
        # Use utility functions for consistent calculations
        today_reviews = get_today_reviews_count(user)
        pending_reviews = get_pending_reviews_count(user)
        success_rate, total_reviews_30_days, _ = calculate_success_rate(user, days=30)
        
        return Response({
            'today_reviews': today_reviews,
            'pending_reviews': pending_reviews,
            'total_content': user.contents.count(),
            'success_rate': success_rate,
            'total_reviews_30_days': total_reviews_30_days,
        })


class ReviewStatsView(APIView):
    """Review statistics view"""
    
    def get(self, request):
        """Get review statistics"""
        user = request.user
        
        # Review result distribution
        result_stats = ReviewHistory.objects.filter(user=user).values('result').annotate(
            count=Count('result')
        )
        
        # Daily review counts (last 30 days)
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        daily_reviews = []
        
        for i in range(30):
            date = thirty_days_ago + timedelta(days=i)
            count = ReviewHistory.objects.filter(
                user=user,
                review_date__date=date
            ).count()
            daily_reviews.append({
                'date': date.isoformat(),
                'count': count
            })
        
        return Response({
            'result_distribution': list(result_stats),
            'daily_reviews': daily_reviews,
        })