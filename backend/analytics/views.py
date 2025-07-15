from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta
from review.models import ReviewHistory, ReviewSchedule


class DashboardView(APIView):
    """Dashboard analytics view"""
    
    def get(self, request):
        """Get dashboard data"""
        user = request.user
        today = timezone.now().date()
        
        # Today's review count
        today_reviews = ReviewSchedule.objects.filter(
            user=user,
            is_active=True,
            next_review_date__date__lte=today
        ).count()
        
        # Pending reviews count
        pending_reviews = ReviewSchedule.objects.filter(
            user=user,
            is_active=True,
            next_review_date__date__gt=today
        ).count()
        
        # Success rate (last 30 days)
        thirty_days_ago = today - timedelta(days=30)
        recent_reviews = ReviewHistory.objects.filter(
            user=user,
            review_date__date__gte=thirty_days_ago
        )
        
        total_reviews = recent_reviews.count()
        successful_reviews = recent_reviews.filter(result='remembered').count()
        success_rate = (successful_reviews / total_reviews * 100) if total_reviews > 0 else 0
        
        return Response({
            'today_reviews': today_reviews,
            'pending_reviews': pending_reviews,
            'total_content': user.contents.count(),
            'success_rate': round(success_rate, 1),
            'total_reviews_30_days': total_reviews,
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