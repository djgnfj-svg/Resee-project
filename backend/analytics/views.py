"""
Simple analytics views for basic learning statistics
"""
from datetime import timedelta
from django.utils import timezone
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from content.models import Content
from review.models import ReviewHistory, ReviewSchedule
from review.utils import calculate_success_rate, get_pending_reviews_count, get_today_reviews_count


class DashboardStatsView(APIView):
    """Basic dashboard statistics"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get basic dashboard statistics"""
        user = request.user

        # Basic counts
        today_reviews = get_today_reviews_count(user)
        pending_reviews = get_pending_reviews_count(user)
        total_content = Content.objects.filter(author=user).count()

        # 30-day success rate
        success_rate, total_reviews_30_days, _ = calculate_success_rate(user, days=30)

        # Simple streak calculation
        streak_days = self._calculate_streak(user)

        return Response({
            'today_reviews': today_reviews,
            'pending_reviews': pending_reviews,
            'total_content': total_content,
            'success_rate': success_rate,
            'total_reviews_30_days': total_reviews_30_days,
            'streak_days': streak_days,
        })

    def _calculate_streak(self, user):
        """Calculate consecutive days of completed reviews"""
        today = timezone.now().date()
        streak = 0

        for i in range(30):  # Check last 30 days max
            check_date = today - timedelta(days=i)
            has_review = ReviewHistory.objects.filter(
                user=user,
                review_date__date=check_date
            ).exists()

            if has_review:
                streak += 1
            else:
                break

        return streak