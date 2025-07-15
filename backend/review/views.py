from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.utils import timezone
from django.conf import settings
from .models import ReviewSchedule, ReviewHistory
from .serializers import ReviewScheduleSerializer, ReviewHistorySerializer


class ReviewScheduleViewSet(viewsets.ModelViewSet):
    """Review schedule viewset"""
    queryset = ReviewSchedule.objects.all()
    serializer_class = ReviewScheduleSerializer
    
    def get_queryset(self):
        return ReviewSchedule.objects.filter(user=self.request.user)


class ReviewHistoryViewSet(viewsets.ModelViewSet):
    """Review history viewset"""
    queryset = ReviewHistory.objects.all()
    serializer_class = ReviewHistorySerializer
    
    def get_queryset(self):
        return ReviewHistory.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class TodayReviewView(APIView):
    """Today's review items"""
    
    def get(self, request):
        """Get today's review items"""
        today = timezone.now().date()
        schedules = ReviewSchedule.objects.filter(
            user=request.user,
            is_active=True,
            next_review_date__date__lte=today
        ).select_related('content', 'content__category').order_by('next_review_date')
        
        # Category filter
        category_slug = request.query_params.get('category_slug', None)
        if category_slug:
            schedules = schedules.filter(content__category__slug=category_slug)
        
        serializer = ReviewScheduleSerializer(schedules, many=True)
        return Response(serializer.data)


class CompleteReviewView(APIView):
    """Complete a review session"""
    
    def post(self, request):
        """Complete a review and update schedule"""
        content_id = request.data.get('content_id')
        result = request.data.get('result')  # 'remembered', 'partial', 'forgot'
        time_spent = request.data.get('time_spent')
        notes = request.data.get('notes', '')
        
        if not content_id or not result:
            return Response(
                {'error': 'content_id and result are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get the review schedule
            schedule = ReviewSchedule.objects.get(
                content_id=content_id,
                user=request.user,
                is_active=True
            )
            
            # Create review history
            history = ReviewHistory.objects.create(
                content=schedule.content,
                user=request.user,
                result=result,
                time_spent=time_spent,
                notes=notes
            )
            
            # Update schedule based on result
            if result == 'remembered':
                # Advance to next interval
                schedule.advance_schedule()
            elif result == 'partial':
                # Stay at current interval but reset date
                intervals = getattr(settings, 'REVIEW_INTERVALS', [1, 3, 7, 14, 30])
                current_interval = intervals[schedule.interval_index]
                schedule.next_review_date = timezone.now() + timezone.timedelta(days=current_interval)
                schedule.save()
            else:  # 'forgot'
                # Reset to first interval
                schedule.reset_schedule()
            
            return Response({
                'message': 'Review completed successfully',
                'next_review_date': schedule.next_review_date,
                'interval_index': schedule.interval_index
            })
            
        except ReviewSchedule.DoesNotExist:
            return Response(
                {'error': 'Review schedule not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )


class CategoryReviewStatsView(APIView):
    """Category-wise review statistics"""
    
    def get(self, request):
        """Get review stats by category"""
        from content.models import Category
        from django.db.models import Count, Q
        
        categories = Category.objects.all()
        result = {}
        
        for category in categories:
            # Today's reviews for this category
            today_reviews = ReviewSchedule.objects.filter(
                user=request.user,
                is_active=True,
                next_review_date__date__lte=timezone.now().date(),
                content__category=category
            ).count()
            
            # Total content in category
            total_content = request.user.contents.filter(category=category).count()
            
            # Success rate for this category (last 30 days)
            from datetime import timedelta
            thirty_days_ago = timezone.now().date() - timedelta(days=30)
            
            category_reviews = ReviewHistory.objects.filter(
                user=request.user,
                content__category=category,
                review_date__date__gte=thirty_days_ago
            )
            
            total_reviews = category_reviews.count()
            successful_reviews = category_reviews.filter(result='remembered').count()
            success_rate = (successful_reviews / total_reviews * 100) if total_reviews > 0 else 0
            
            result[category.slug] = {
                'category': category.name,
                'today_reviews': today_reviews,
                'total_content': total_content,
                'success_rate': round(success_rate, 1),
                'total_reviews_30_days': total_reviews,
            }
        
        return Response(result)