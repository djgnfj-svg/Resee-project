from collections import defaultdict
from datetime import datetime, timedelta

from django.db.models import Count
from django.utils import timezone
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from content.models import Category, Content
from review.models import ReviewHistory, ReviewSchedule
from review.utils import (calculate_success_rate, get_pending_reviews_count,
                          get_today_reviews_count)


class DashboardView(APIView):
    """Dashboard analytics view"""
    
    @swagger_auto_schema(
        operation_summary="대시보드 데이터 조회",
        operation_description="""
        사용자의 대시보드 분석 데이터를 제공합니다.
        
        **응답 데이터:**
        - `today_reviews`: 오늘 예정된 복습 수
        - `pending_reviews`: 밀린 복습 수
        - `total_content`: 총 학습 콘텐츠 수
        - `success_rate`: 30일간 복습 성공률 (%)
        - `total_reviews_30_days`: 30일간 총 복습 수
        - `streak_days`: 연속 학습 일수
        """,
        tags=['Analytics'],
        responses={
            200: openapi.Response(
                description="대시보드 데이터",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'today_reviews': openapi.Schema(type=openapi.TYPE_INTEGER, description="오늘 예정된 복습 수"),
                        'pending_reviews': openapi.Schema(type=openapi.TYPE_INTEGER, description="밀린 복습 수"),
                        'total_content': openapi.Schema(type=openapi.TYPE_INTEGER, description="총 학습 콘텐츠 수"),
                        'success_rate': openapi.Schema(type=openapi.TYPE_NUMBER, description="30일간 복습 성공률 (%)"),
                        'total_reviews_30_days': openapi.Schema(type=openapi.TYPE_INTEGER, description="30일간 총 복습 수"),
                        'streak_days': openapi.Schema(type=openapi.TYPE_INTEGER, description="연속 학습 일수"),
                    }
                )
            ),
            401: "인증 필요",
        }
    )
    def get(self, request):
        """Get dashboard data - optimized version"""
        user = request.user
        
        # Use utility functions for consistent calculations
        today_reviews = get_today_reviews_count(user)
        pending_reviews = get_pending_reviews_count(user)
        success_rate, total_reviews_30_days, _ = calculate_success_rate(user, days=30)
        
        # Calculate streak
        streak_days = self._calculate_review_streak(user)
        
        return Response({
            'today_reviews': today_reviews,
            'pending_reviews': pending_reviews,
            'total_content': user.contents.count(),
            'success_rate': success_rate,
            'total_reviews_30_days': total_reviews_30_days,
            'streak_days': streak_days,
        })
    
    def _calculate_review_streak(self, user):
        """Calculate consecutive days of reviews"""
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


class ReviewStatsView(APIView):
    """Enhanced review statistics view"""
    
    @swagger_auto_schema(
        operation_summary="복습 통계 조회",
        operation_description="""
        포괄적인 복습 통계 데이터를 제공합니다.
        
        **응답 데이터:**
        - `result_distribution`: 복습 결과 분포 (전체 기간 / 최근 30일)
        - `daily_reviews`: 일별 복습 데이터 (최근 30일)
        - `weekly_performance`: 주간 성과 지표 (최근 4주)
        - `trends`: 복습 트렌드 분석
        """,
        tags=['Analytics'],
        responses={
            200: openapi.Response(
                description="복습 통계 데이터",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'result_distribution': openapi.Schema(type=openapi.TYPE_OBJECT, description="복습 결과 분포"),
                        'daily_reviews': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description="일별 복습 데이터"),
                        'weekly_performance': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description="주간 성과 지표"),
                        'trends': openapi.Schema(type=openapi.TYPE_OBJECT, description="복습 트렌드 분석"),
                    }
                )
            ),
            401: "인증 필요",
        }
    )
    def get(self, request):
        """Get comprehensive review statistics"""
        user = request.user
        
        # Review result distribution with percentages and temporal context
        result_stats = self._get_result_distribution(user)
        
        # Enhanced daily review data with success rates
        daily_reviews = self._get_daily_reviews_with_performance(user)
        
        # Weekly performance metrics
        weekly_performance = self._get_weekly_performance(user)
        
        # Review trends
        trends = self._get_review_trends(user)
        
        return Response({
            'result_distribution': result_stats,
            'daily_reviews': daily_reviews,
            'weekly_performance': weekly_performance,
            'trends': trends,
        })
    
    def _get_result_distribution(self, user):
        """Get result distribution with percentages and context"""
        # Last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # All time stats
        all_time_stats = ReviewHistory.objects.filter(user=user).values('result').annotate(
            count=Count('result')
        )
        
        # Recent stats (last 30 days)
        recent_stats = ReviewHistory.objects.filter(
            user=user,
            review_date__gte=thirty_days_ago
        ).values('result').annotate(
            count=Count('result')
        )
        
        # Calculate totals and percentages
        all_time_total = sum(item['count'] for item in all_time_stats)
        recent_total = sum(item['count'] for item in recent_stats)
        
        # Process results
        result_mapping = {
            'remembered': '기억함',
            'partial': '애매함', 
            'forgot': '모름'
        }
        
        all_time_processed = []
        recent_processed = []
        
        for result_type in ['remembered', 'partial', 'forgot']:
            # All time
            all_time_count = next((item['count'] for item in all_time_stats if item['result'] == result_type), 0)
            all_time_percentage = (all_time_count / all_time_total * 100) if all_time_total > 0 else 0
            
            # Recent
            recent_count = next((item['count'] for item in recent_stats if item['result'] == result_type), 0)
            recent_percentage = (recent_count / recent_total * 100) if recent_total > 0 else 0
            
            all_time_processed.append({
                'result': result_type,
                'name': result_mapping[result_type],
                'count': all_time_count,
                'percentage': round(all_time_percentage, 1)
            })
            
            recent_processed.append({
                'result': result_type,
                'name': result_mapping[result_type],
                'count': recent_count,
                'percentage': round(recent_percentage, 1)
            })
        
        return {
            'all_time': all_time_processed,
            'recent_30_days': recent_processed,
            'all_time_total': all_time_total,
            'recent_total': recent_total
        }
    
    def _get_daily_reviews_with_performance(self, user):
        """Get daily reviews with success rates and performance metrics"""
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        daily_data = []
        
        for i in range(30):
            date = thirty_days_ago + timedelta(days=i)
            
            # Get reviews for this date
            day_reviews = ReviewHistory.objects.filter(
                user=user,
                review_date__date=date
            )
            
            total_count = day_reviews.count()
            remembered_count = day_reviews.filter(result='remembered').count()
            success_rate = (remembered_count / total_count * 100) if total_count > 0 else 0
            
            daily_data.append({
                'date': date.isoformat(),
                'count': total_count,
                'success_rate': round(success_rate, 1),
                'remembered': remembered_count,
                'partial': day_reviews.filter(result='partial').count(),
                'forgot': day_reviews.filter(result='forgot').count(),
            })
        
        return daily_data
    
    def _get_weekly_performance(self, user):
        """Get weekly performance metrics with trends"""
        today = timezone.now().date()
        weeks_data = []
        
        for week_offset in range(4):  # Last 4 weeks
            week_start = today - timedelta(days=today.weekday() + 7 * week_offset)
            week_end = week_start + timedelta(days=6)
            
            # Get reviews for this week
            week_reviews = ReviewHistory.objects.filter(
                user=user,
                review_date__date__range=[week_start, week_end]
            )
            
            total_count = week_reviews.count()
            remembered_count = week_reviews.filter(result='remembered').count()
            success_rate = (remembered_count / total_count * 100) if total_count > 0 else 0
            
            # Calculate consistency (days with reviews)
            days_with_reviews = 0
            for day_offset in range(7):
                check_date = week_start + timedelta(days=day_offset)
                if week_reviews.filter(review_date__date=check_date).exists():
                    days_with_reviews += 1
            
            consistency = (days_with_reviews / 7 * 100)
            
            weeks_data.append({
                'week_start': week_start.isoformat(),
                'week_end': week_end.isoformat(),
                'week_label': f"{week_start.strftime('%m/%d')} - {week_end.strftime('%m/%d')}",
                'total_reviews': total_count,
                'success_rate': round(success_rate, 1),
                'consistency': round(consistency, 1),
                'days_active': days_with_reviews,
                'remembered': remembered_count,
                'partial': week_reviews.filter(result='partial').count(),
                'forgot': week_reviews.filter(result='forgot').count(),
            })
        
        return list(reversed(weeks_data))  # Most recent first
    
    def _get_review_trends(self, user):
        """Get review trends and insights"""
        # Calculate trends for last 30 days vs previous 30 days
        today = timezone.now().date()
        
        # Current period (last 30 days)
        current_start = today - timedelta(days=30)
        current_reviews = ReviewHistory.objects.filter(
            user=user,
            review_date__date__gte=current_start
        )
        
        # Previous period (30 days before that)
        previous_start = current_start - timedelta(days=30)
        previous_reviews = ReviewHistory.objects.filter(
            user=user,
            review_date__date__range=[previous_start, current_start]
        )
        
        # Calculate metrics
        current_total = current_reviews.count()
        previous_total = previous_reviews.count()
        
        current_success_rate = (current_reviews.filter(result='remembered').count() / current_total * 100) if current_total > 0 else 0
        previous_success_rate = (previous_reviews.filter(result='remembered').count() / previous_total * 100) if previous_total > 0 else 0
        
        # Calculate changes
        review_count_change = current_total - previous_total
        success_rate_change = current_success_rate - previous_success_rate
        
        return {
            'review_count_change': review_count_change,
            'success_rate_change': round(success_rate_change, 1),
            'current_period_total': current_total,
            'previous_period_total': previous_total,
            'current_success_rate': round(current_success_rate, 1),
            'previous_success_rate': round(previous_success_rate, 1),
        }


class AdvancedAnalyticsView(APIView):
    """Advanced learning analytics data provider"""
    
    @swagger_auto_schema(
        operation_summary="고급 학습 분석 데이터 조회",
        operation_description="""
        종합적인 학습 분석 데이터를 제공합니다.
        
        **응답 데이터:**
        - `learning_insights`: 학습 인사이트 (총 콘텐츠, 총 복습, 성공률 등)
        - `category_performance`: 카테고리별 성과 분석
        - `study_patterns`: 학습 패턴 분석 (시간대별, 요일별)
        - `achievement_stats`: 성취 통계 (연속 학습, 완벽 세션 등)
        - `recommendations`: 개인화된 학습 추천사항
        """,
        tags=['Analytics'],
        responses={
            200: openapi.Response(
                description="고급 학습 분석 데이터",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'learning_insights': openapi.Schema(type=openapi.TYPE_OBJECT, description="학습 인사이트"),
                        'category_performance': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description="카테고리별 성과"),
                        'study_patterns': openapi.Schema(type=openapi.TYPE_OBJECT, description="학습 패턴"),
                        'achievement_stats': openapi.Schema(type=openapi.TYPE_OBJECT, description="성취 통계"),
                        'recommendations': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description="학습 추천사항"),
                    }
                )
            ),
            401: "인증 필요",
        }
    )
    def get(self, request):
        """Return comprehensive learning analytics data"""
        user = request.user
        
        return Response({
            'learning_insights': self._get_learning_insights(user),
            'category_performance': self._get_category_performance(user),
            'study_patterns': self._get_study_patterns(user),
            'achievement_stats': self._get_achievement_stats(user),
            'performance_metrics': self._get_performance_metrics(user),
            'recommendations': self._get_recommendations(user),
        })
    
    def _get_learning_insights(self, user):
        """Learning insights data"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        # Overall statistics
        total_content = user.contents.count()
        total_reviews = ReviewHistory.objects.filter(user=user).count()
        
        # Recent 30 days activity
        recent_reviews = ReviewHistory.objects.filter(
            user=user,
            review_date__gte=thirty_days_ago
        )
        
        # Recent 7 days activity
        week_reviews = ReviewHistory.objects.filter(
            user=user,
            review_date__gte=seven_days_ago
        )
        
        # Success rate calculation
        recent_success_rate = (
            recent_reviews.filter(result='remembered').count() / 
            recent_reviews.count() * 100
        ) if recent_reviews.count() > 0 else 0
        
        week_success_rate = (
            week_reviews.filter(result='remembered').count() / 
            week_reviews.count() * 100
        ) if week_reviews.count() > 0 else 0
        
        # Average review interval calculation
        avg_interval = self._calculate_average_interval(user)
        
        return {
            'total_content': total_content,
            'total_reviews': total_reviews,
            'recent_30d_reviews': recent_reviews.count(),
            'recent_7d_reviews': week_reviews.count(),
            'recent_success_rate': round(recent_success_rate, 1),
            'week_success_rate': round(week_success_rate, 1),
            'average_interval_days': avg_interval,
            'streak_days': self._calculate_detailed_streak(user),
        }
    
    def _get_category_performance(self, user):
        """Category-wise performance analysis"""
        categories = Category.objects.filter(user=user)
        category_stats = []
        
        for category in categories:
            # Content and review statistics per category
            content_count = Content.objects.filter(category=category).count()
            
            # All reviews for category content
            category_reviews = ReviewHistory.objects.filter(
                content__category=category
            )
            
            if category_reviews.exists():
                total_reviews = category_reviews.count()
                remembered_count = category_reviews.filter(result='remembered').count()
                success_rate = (remembered_count / total_reviews * 100)
                
                # Recent 30 days performance
                recent_reviews = category_reviews.filter(
                    review_date__gte=timezone.now() - timedelta(days=30)
                )
                recent_success_rate = (
                    recent_reviews.filter(result='remembered').count() / 
                    recent_reviews.count() * 100
                ) if recent_reviews.count() > 0 else 0
                
                # Difficulty calculation (based on failure rate)
                difficulty = 100 - success_rate
                
                category_stats.append({
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                    'content_count': content_count,
                    'total_reviews': total_reviews,
                    'success_rate': round(success_rate, 1),
                    'recent_success_rate': round(recent_success_rate, 1),
                    'difficulty_level': round(difficulty, 1),
                    'mastery_level': self._calculate_mastery_level(success_rate),
                })
        
        return sorted(category_stats, key=lambda x: x['success_rate'], reverse=True)
    
    def _get_study_patterns(self, user):
        """Study pattern analysis"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Hourly learning patterns
        hourly_pattern = defaultdict(int)
        reviews = ReviewHistory.objects.filter(
            user=user,
            review_date__gte=thirty_days_ago
        )
        
        for review in reviews:
            hour = review.review_date.hour
            hourly_pattern[hour] += 1
        
        # Daily learning patterns
        daily_pattern = defaultdict(int)
        for review in reviews:
            weekday = review.review_date.weekday()  # 0=Monday, 6=Sunday
            daily_pattern[weekday] += 1
        
        # Pattern data organization
        hourly_data = [
            {'hour': hour, 'count': hourly_pattern[hour]}
            for hour in range(24)
        ]
        
        daily_labels = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        daily_data = [
            {'day': daily_labels[day], 'count': daily_pattern[day]}
            for day in range(7)
        ]
        
        # Optimal study time recommendations
        best_hour = max(hourly_pattern.items(), key=lambda x: x[1])[0] if hourly_pattern else 9
        best_day = max(daily_pattern.items(), key=lambda x: x[1])[0] if daily_pattern else 0
        
        return {
            'hourly_pattern': hourly_data,
            'daily_pattern': daily_data,
            'recommended_hour': best_hour,
            'recommended_day': daily_labels[best_day],
            'total_study_sessions': len(reviews),
        }
    
    def _get_achievement_stats(self, user):
        """Achievement statistics"""
        # Consecutive study days calculation
        current_streak = self._calculate_detailed_streak(user)
        max_streak = self._calculate_max_streak(user)
        
        # Perfect review sessions (all remembered)
        perfect_sessions = self._count_perfect_sessions(user)
        
        # Category mastery (90% or higher success rate)
        mastered_categories = self._count_mastered_categories(user)
        
        # Monthly goal achievement rate
        monthly_target = 100  # Default goal: 100 reviews per month
        current_month_reviews = ReviewHistory.objects.filter(
            user=user,
            review_date__month=timezone.now().month,
            review_date__year=timezone.now().year
        ).count()
        
        monthly_progress = min(100, (current_month_reviews / monthly_target * 100))
        
        return {
            'current_streak': current_streak,
            'max_streak': max_streak,
            'perfect_sessions': perfect_sessions,
            'mastered_categories': mastered_categories,
            'monthly_progress': round(monthly_progress, 1),
            'monthly_target': monthly_target,
            'monthly_completed': current_month_reviews,
        }
    
    def _get_recommendations(self, user):
        """Personalized learning recommendations"""
        recommendations = []
        
        # Category performance analysis
        category_performance = self._get_category_performance(user)
        
        # Weak category recommendations
        weak_categories = [cat for cat in category_performance if cat['success_rate'] < 70]
        if weak_categories:
            recommendations.append({
                'type': 'weak_category',
                'title': 'Focus Study Required',
                'message': f"{weak_categories[0]['name']} category needs more review.",
                'action': 'review_category',
                'category_id': weak_categories[0]['id'],
            })
        
        # Study pattern based recommendations
        study_patterns = self._get_study_patterns(user)
        if study_patterns['total_study_sessions'] > 0:
            recommendations.append({
                'type': 'optimal_time',
                'title': 'Optimal Study Time',
                'message': f"Around {study_patterns['recommended_hour']}:00 is your most active study time.",
                'action': 'schedule_reminder',
                'hour': study_patterns['recommended_hour'],
            })
        
        # Consecutive study day encouragement
        achievement_stats = self._get_achievement_stats(user)
        if achievement_stats['current_streak'] >= 7:
            recommendations.append({
                'type': 'streak_celebration',
                'title': 'Study Streak Achievement!',
                'message': f"You've been studying for {achievement_stats['current_streak']} consecutive days. Great job!",
                'action': 'continue_streak',
            })
        
        return recommendations
    
    def _calculate_average_interval(self, user):
        """Calculate average review interval"""
        from review.utils import get_review_intervals
        
        schedules = ReviewSchedule.objects.filter(user=user)
        if schedules.exists():
            intervals = get_review_intervals(user)
            total_interval = 0
            valid_schedules = 0
            
            for schedule in schedules:
                if schedule.interval_index < len(intervals):
                    total_interval += intervals[schedule.interval_index]
                    valid_schedules += 1
            
            if valid_schedules > 0:
                return round(total_interval / valid_schedules, 1)
        return 0
    
    def _calculate_detailed_streak(self, user):
        """Calculate detailed consecutive study days"""
        today = timezone.now().date()
        streak = 0
        
        for i in range(365):  # Maximum 1 year
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
    
    def _calculate_max_streak(self, user):
        """Calculate maximum consecutive study days"""
        reviews = ReviewHistory.objects.filter(user=user).order_by('review_date')
        if not reviews.exists():
            return 0
        
        max_streak = 0
        current_streak = 1
        prev_date = reviews.first().review_date.date()
        
        for review in reviews[1:]:
            current_date = review.review_date.date()
            if (current_date - prev_date).days == 1:
                current_streak += 1
            else:
                max_streak = max(max_streak, current_streak)
                current_streak = 1
            prev_date = current_date
        
        return max(max_streak, current_streak)
    
    def _count_perfect_sessions(self, user):
        """Count perfect review sessions"""
        # Calculate days when all reviews were 'remembered'
        thirty_days_ago = timezone.now().date() - timedelta(days=30)
        perfect_days = 0
        
        for i in range(30):
            check_date = thirty_days_ago + timedelta(days=i)
            day_reviews = ReviewHistory.objects.filter(
                user=user,
                review_date__date=check_date
            )
            
            if day_reviews.exists():
                total_count = day_reviews.count()
                remembered_count = day_reviews.filter(result='remembered').count()
                
                if total_count == remembered_count:
                    perfect_days += 1
        
        return perfect_days
    
    def _count_mastered_categories(self, user):
        """Count mastered categories (90% or higher success rate)"""
        category_performance = self._get_category_performance(user)
        return len([cat for cat in category_performance if cat['success_rate'] >= 90])
    
    def _calculate_mastery_level(self, success_rate):
        """Calculate mastery level"""
        if success_rate >= 90:
            return 'expert'
        elif success_rate >= 75:
            return 'advanced'
        elif success_rate >= 60:
            return 'intermediate'
        elif success_rate >= 40:
            return 'beginner'
        else:
            return 'novice'
    
    def _get_performance_metrics(self, user):
        """Performance metrics for dashboard"""
        # Get current streak
        current_streak = self._calculate_detailed_streak(user)
        longest_streak = self._calculate_max_streak(user)
        
        # Get total reviews
        total_reviews = ReviewHistory.objects.filter(user=user).count()
        
        # Calculate average retention (remembered / total)
        total_remembered = ReviewHistory.objects.filter(
            user=user, 
            result='remembered'
        ).count()
        average_retention = (total_remembered / total_reviews * 100) if total_reviews > 0 else 0
        
        # Calculate study efficiency (success rate in recent 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_reviews = ReviewHistory.objects.filter(
            user=user,
            review_date__gte=thirty_days_ago
        )
        study_efficiency = (
            recent_reviews.filter(result='remembered').count() / 
            recent_reviews.count() * 100
        ) if recent_reviews.count() > 0 else 0
        
        # Get weekly goal from user settings
        weekly_goal = user.weekly_goal
        
        # Calculate current week progress
        week_start = timezone.now().date() - timedelta(days=timezone.now().weekday())
        week_reviews = ReviewHistory.objects.filter(
            user=user,
            review_date__gte=week_start
        ).count()
        
        return {
            'currentStreak': current_streak,
            'longestStreak': longest_streak,
            'totalReviews': total_reviews,
            'averageRetention': round(average_retention, 1),
            'studyEfficiency': round(study_efficiency, 1),
            'weeklyGoal': weekly_goal,
            'weeklyProgress': week_reviews,
        }


class LearningCalendarView(APIView):
    """Learning calendar and heatmap data"""
    
    @swagger_auto_schema(
        operation_summary="학습 캘린더 데이터 조회",
        operation_description="""
        GitHub 스타일의 학습 캘린더 히트맵 데이터를 제공합니다.
        
        **응답 데이터:**
        - `calendar_data`: 365일간의 일별 학습 데이터
        - `monthly_summary`: 월별 요약 통계 (최근 12개월)
        - `total_active_days`: 총 활성 학습일 수
        - `best_day`: 최고 복습 수를 기록한 날
        
        **강도 레벨:**
        - 0: 복습 없음
        - 1: 1-9개 복습
        - 2: 10-14개 복습  
        - 3: 15-19개 복습
        - 4: 20개 이상 복습
        """,
        tags=['Analytics'],
        responses={
            200: openapi.Response(
                description="학습 캘린더 데이터",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'calendar_data': openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    'date': openapi.Schema(type=openapi.TYPE_STRING, description="날짜 (ISO 형식)"),
                                    'count': openapi.Schema(type=openapi.TYPE_INTEGER, description="복습 수"),
                                    'success_rate': openapi.Schema(type=openapi.TYPE_NUMBER, description="성공률 (%)"),
                                    'intensity': openapi.Schema(type=openapi.TYPE_INTEGER, description="강도 레벨 (0-4)"),
                                    'remembered': openapi.Schema(type=openapi.TYPE_INTEGER, description="기억함 수"),
                                    'partial': openapi.Schema(type=openapi.TYPE_INTEGER, description="애매함 수"),
                                    'forgot': openapi.Schema(type=openapi.TYPE_INTEGER, description="모름 수"),
                                }
                            ),
                            description="365일간의 일별 학습 데이터"
                        ),
                        'monthly_summary': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT), description="월별 요약 통계"),
                        'total_active_days': openapi.Schema(type=openapi.TYPE_INTEGER, description="총 활성 학습일 수"),
                        'best_day': openapi.Schema(type=openapi.TYPE_OBJECT, description="최고 복습 수를 기록한 날"),
                    }
                )
            ),
            401: "인증 필요",
        }
    )
    def get(self, request):
        """Return calendar heatmap data"""
        user = request.user
        
        # Past 365 days data (including today)
        today = timezone.now().date()
        one_year_ago = today - timedelta(days=364)  # 364 days ago + today = 365 days
        calendar_data = []
        
        for i in range(365):
            date = one_year_ago + timedelta(days=i)
            
            # Review data for this date
            day_reviews = ReviewHistory.objects.filter(
                user=user,
                review_date__date=date
            )
            
            total_reviews = day_reviews.count()
            remembered_count = day_reviews.filter(result='remembered').count()
            success_rate = (remembered_count / total_reviews * 100) if total_reviews > 0 else 0
            
            # Intensity calculation (0-4 levels)
            intensity = 0
            if total_reviews > 0:
                if total_reviews >= 20:
                    intensity = 4
                elif total_reviews >= 15:
                    intensity = 3
                elif total_reviews >= 10:
                    intensity = 2
                else:
                    intensity = 1
            
            calendar_data.append({
                'date': date.isoformat(),
                'count': total_reviews,
                'success_rate': round(success_rate, 1),
                'intensity': intensity,
                'remembered': remembered_count,
                'partial': day_reviews.filter(result='partial').count(),
                'forgot': day_reviews.filter(result='forgot').count(),
            })
        
        # Monthly summary statistics
        monthly_summary = self._get_monthly_summary(user, calendar_data)
        
        return Response({
            'calendar_data': calendar_data,
            'monthly_summary': monthly_summary,
            'total_active_days': len([d for d in calendar_data if d['count'] > 0]),
            'best_day': max(calendar_data, key=lambda x: x['count']) if calendar_data else None,
        })
    
    def _get_monthly_summary(self, user, calendar_data):
        """Monthly summary statistics"""
        monthly_stats = defaultdict(lambda: {
            'total_reviews': 0,
            'active_days': 0,
            'total_remembered': 0,
        })
        
        for day_data in calendar_data:
            date = datetime.fromisoformat(day_data['date']).date()
            month_key = f"{date.year}-{date.month:02d}"
            
            monthly_stats[month_key]['total_reviews'] += day_data['count']
            if day_data['count'] > 0:
                monthly_stats[month_key]['active_days'] += 1
            monthly_stats[month_key]['total_remembered'] += day_data['remembered']
        
        # Return only the most recent 12 months
        result = []
        for month_key in sorted(monthly_stats.keys())[-12:]:
            stats = monthly_stats[month_key]
            success_rate = (
                stats['total_remembered'] / stats['total_reviews'] * 100
            ) if stats['total_reviews'] > 0 else 0
            
            result.append({
                'month': month_key,
                'total_reviews': stats['total_reviews'],
                'active_days': stats['active_days'],
                'success_rate': round(success_rate, 1),
            })
        
        return result"""
Business Intelligence API views
"""
import logging
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema

from .models import LearningPattern, ContentEffectiveness, SubscriptionAnalytics
from .serializers import (
    LearningInsightsSerializer, ContentAnalyticsSerializer, 
    SubscriptionInsightsSerializer, BusinessDashboardSerializer,
    PerformanceTrendSerializer, LearningRecommendationSerializer
)
from .services.analytics_engine import LearningAnalyticsEngine, BusinessMetricsEngine
from .services.recommendation_engine import RecommendationEngine
from .services.subscription_analyzer import SubscriptionAnalyzer

logger = logging.getLogger(__name__)


class LearningInsightsView(APIView):
    """
    Get comprehensive learning insights for the authenticated user
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="사용자 학습 인사이트",
        operation_description="""
        사용자의 학습 패턴과 성과를 분석하여 종합적인 인사이트를 제공합니다.
        
        **제공하는 인사이트:**
        - 총 학습 일수 및 연속 학습 기록
        - 일평균 복습 수 및 성공률
        - 가장 생산적인 시간대
        - 총 학습 시간 및 일관성 점수
        """,
        manual_parameters=[
            openapi.Parameter('days', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, 
                            description='분석 기간 (일수)', default=30),
        ],
        responses={
            200: LearningInsightsSerializer,
            401: "인증 필요"
        },
        tags=['Business Intelligence - Learning']
    )
    def get(self, request):
        days = int(request.query_params.get('days', 30))
        engine = LearningAnalyticsEngine(request.user)
        insights = engine.get_learning_insights(days)
        
        serializer = LearningInsightsSerializer(insights)
        return Response(serializer.data)


class ContentAnalyticsView(APIView):
    """
    Get content effectiveness analytics for the authenticated user
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="콘텐츠 효율성 분석",
        operation_description="""
        사용자가 생성한 콘텐츠의 학습 효율성과 패턴을 분석합니다.
        
        **분석 항목:**
        - 마스터한 콘텐츠 vs 어려워하는 콘텐츠
        - 평균 마스터 소요 시간
        - 가장/최소 효과적인 콘텐츠 유형
        - 카테고리별 성과 분석
        """,
        responses={
            200: ContentAnalyticsSerializer,
            401: "인증 필요"
        },
        tags=['Business Intelligence - Content']
    )
    def get(self, request):
        engine = LearningAnalyticsEngine(request.user)
        analytics = engine.get_content_analytics()
        
        serializer = ContentAnalyticsSerializer(analytics)
        return Response(serializer.data)


class PerformanceTrendView(APIView):
    """
    Get daily performance trends for the authenticated user
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="학습 성과 트렌드",
        operation_description="""
        일별 학습 성과의 변화 추이를 제공합니다.
        
        **트렌드 데이터:**
        - 일별 성공률 변화
        - 완료한 복습 수
        - 학습 시간 추이
        - 난이도 트렌드 및 참여도 점수
        """,
        manual_parameters=[
            openapi.Parameter('days', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, 
                            description='분석 기간 (일수)', default=30),
        ],
        responses={
            200: PerformanceTrendSerializer(many=True),
            401: "인증 필요"
        },
        tags=['Business Intelligence - Trends']
    )
    def get(self, request):
        days = int(request.query_params.get('days', 30))
        engine = LearningAnalyticsEngine(request.user)
        trends = engine.get_performance_trends(days)
        
        serializer = PerformanceTrendSerializer(trends, many=True)
        return Response(serializer.data)


class LearningRecommendationsView(APIView):
    """
    Get AI-powered learning recommendations
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="AI 학습 추천",
        operation_description="""
        사용자의 학습 패턴을 분석하여 개인화된 추천사항을 제공합니다.
        
        **추천 유형:**
        - 학습 스케줄 최적화
        - 콘텐츠 추천
        - 난이도 조정 제안
        - 참여도 개선 방안
        """,
        responses={
            200: LearningRecommendationSerializer(many=True),
            401: "인증 필요"
        },
        tags=['Business Intelligence - Recommendations']
    )
    def get(self, request):
        try:
            engine = RecommendationEngine(request.user)
            recommendations = engine.generate_recommendations()
            
            serializer = LearningRecommendationSerializer(recommendations, many=True)
            return Response(serializer.data)
        except Exception as e:
            logger.error(f"Error generating recommendations for user {request.user.id}: {e}")
            return Response(
                {"detail": "추천사항을 생성하는 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SubscriptionInsightsView(APIView):
    """
    Get subscription analytics and insights for the authenticated user
    """
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_summary="구독 인사이트",
        operation_description="""
        사용자의 구독 사용 패턴과 가치 분석을 제공합니다.
        
        **분석 항목:**
        - 현재 구독 티어 및 사용 기간
        - 기능 활용률
        - 업그레이드 추천
        - 복습당 비용 효율성
        """,
        responses={
            200: SubscriptionInsightsSerializer,
            401: "인증 필요"
        },
        tags=['Business Intelligence - Subscription']
    )
    def get(self, request):
        try:
            # Get current subscription
            subscription = getattr(request.user, 'subscription', None)
            if not subscription:
                return Response({
                    'current_tier': 'FREE',
                    'tier_duration_days': 0,
                    'feature_utilization_rate': 0.0,
                    'upgrade_recommendation': '기본 기능을 더 활용해보세요',
                    'usage_efficiency_score': 0.0,
                    'cost_per_review': 0.0,
                    'projected_monthly_value': 0.0,
                })
            
            # Calculate subscription metrics
            tier_duration = (timezone.now().date() - subscription.created_at.date()).days
            
            # Feature utilization (simplified calculation)
            engine = LearningAnalyticsEngine(request.user)
            insights = engine.get_learning_insights(30)
            
            # Estimate feature utilization based on activity
            feature_usage_score = min(100, 
                (insights['average_daily_reviews'] * 10) + 
                (insights['learning_consistency_score'] * 0.5)
            )
            
            # Usage efficiency (reviews per day vs subscription cost)
            monthly_cost = float(subscription.amount_paid or 0)
            daily_cost = monthly_cost / 30 if monthly_cost > 0 else 0
            cost_per_review = daily_cost / insights['average_daily_reviews'] if insights['average_daily_reviews'] > 0 else 0
            
            # Projected value based on learning progress
            projected_value = insights['learning_consistency_score'] * 2  # Simplified calculation
            
            # Upgrade recommendation logic
            if subscription.tier == 'FREE' and insights['average_daily_reviews'] > 5:
                upgrade_rec = 'BASIC 플랜으로 업그레이드하여 더 많은 기능을 이용하세요'
            elif subscription.tier == 'BASIC' and insights['average_daily_reviews'] > 15:
                upgrade_rec = 'PRO 플랜으로 업그레이드하여 AI 기능을 무제한 이용하세요'
            else:
                upgrade_rec = '현재 플랜이 사용 패턴에 적합합니다'
            
            data = {
                'current_tier': subscription.tier,
                'tier_duration_days': tier_duration,
                'feature_utilization_rate': round(feature_usage_score, 2),
                'upgrade_recommendation': upgrade_rec,
                'usage_efficiency_score': round(feature_usage_score * 0.8, 2),
                'cost_per_review': round(cost_per_review, 2),
                'projected_monthly_value': round(projected_value, 2),
            }
            
            serializer = SubscriptionInsightsSerializer(data)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error generating subscription insights for user {request.user.id}: {e}")
            return Response(
                {"detail": "구독 분석 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BusinessDashboardView(APIView):
    """
    Get comprehensive business metrics (Admin only)
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="비즈니스 대시보드",
        operation_description="""
        전체 서비스의 비즈니스 메트릭과 KPI를 제공합니다.
        
        **관리자 전용 기능**
        
        **제공 메트릭:**
        - 사용자 및 매출 통계
        - 사용자 참여도 및 유지율
        - 콘텐츠 생성 및 완료율
        - 구독 전환율 및 이탈률
        - AI 사용률 및 비용 효율성
        - 시스템 성능 지표
        """,
        manual_parameters=[
            openapi.Parameter('days', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, 
                            description='분석 기간 (일수)', default=30),
        ],
        responses={
            200: BusinessDashboardSerializer,
            401: "인증 필요",
            403: "관리자 권한 필요"
        },
        tags=['Business Intelligence - Admin']
    )
    def get(self, request):
        try:
            days = int(request.query_params.get('days', 30))
            engine = BusinessMetricsEngine()
            dashboard_data = engine.get_business_dashboard(days)
            
            serializer = BusinessDashboardSerializer(dashboard_data)
            return Response(serializer.data)
            
        except Exception as e:
            logger.error(f"Error generating business dashboard: {e}")
            return Response(
                {"detail": "비즈니스 대시보드 생성 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@swagger_auto_schema(
    method='post',
    operation_summary="학습 패턴 데이터 업데이트",
    operation_description="""
    사용자의 일일 학습 패턴 데이터를 업데이트합니다.
    
    **자동으로 수집되는 데이터:**
    - 생성된 콘텐츠 수
    - 완료된 복습 수
    - AI 질문 생성 수
    - 세션 시간 및 성공률
    """,
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        properties={
            'date': openapi.Schema(type=openapi.TYPE_STRING, format='date'),
            'session_duration_minutes': openapi.Schema(type=openapi.TYPE_INTEGER),
            'peak_activity_hour': openapi.Schema(type=openapi.TYPE_INTEGER),
        }
    ),
    responses={
        200: "학습 패턴 업데이트 완료",
        400: "잘못된 요청",
        401: "인증 필요"
    },
    tags=['Business Intelligence - Data']
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_learning_pattern(request):
    """
    Update daily learning pattern data for the authenticated user
    """
    try:
        date_str = request.data.get('date', timezone.now().date().isoformat())
        session_duration = request.data.get('session_duration_minutes', 0)
        peak_hour = request.data.get('peak_activity_hour')
        
        # Parse date
        from datetime import datetime
        target_date = datetime.fromisoformat(date_str).date()
        
        # Get or create learning pattern
        pattern, created = LearningPattern.objects.get_or_create(
            user=request.user,
            date=target_date,
            defaults={
                'session_duration_minutes': session_duration,
                'peak_activity_hour': peak_hour,
            }
        )
        
        if not created:
            # Update existing record
            if session_duration > 0:
                pattern.session_duration_minutes += session_duration
            if peak_hour is not None:
                pattern.peak_activity_hour = peak_hour
            pattern.save()
        
        return Response({
            "message": "학습 패턴이 업데이트되었습니다.",
            "date": target_date,
            "session_duration_minutes": pattern.session_duration_minutes
        })
        
    except Exception as e:
        logger.error(f"Error updating learning pattern for user {request.user.id}: {e}")
        return Response(
            {"detail": "학습 패턴 업데이트 중 오류가 발생했습니다."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class SubscriptionAnalysisView(APIView):
    """
    Subscription analysis and conversion insights (Admin only)
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="구독 분석",
        operation_description="""
        전체 서비스의 구독 전환 및 이탈 패턴을 분석합니다.
        
        **관리자 전용 기능**
        
        **분석 유형:**
        - conversion-funnel: 전환 깔대기 분석
        - churn-patterns: 이탈 패턴 분석  
        - customer-lifetime-value: 고객 생애 가치
        - insights-report: 종합 인사이트 보고서
        """,
        manual_parameters=[
            openapi.Parameter('analysis_type', openapi.IN_QUERY, type=openapi.TYPE_STRING, 
                            required=True, description='분석 유형'),
            openapi.Parameter('days', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, 
                            description='분석 기간 (일수)', default=30),
            openapi.Parameter('tier', openapi.IN_QUERY, type=openapi.TYPE_STRING, 
                            description='구독 티어 필터 (CLV 분석 시)'),
        ],
        responses={
            200: "분석 결과",
            400: "잘못된 요청",
            401: "인증 필요",
            403: "관리자 권한 필요"
        },
        tags=['Business Intelligence - Subscription']
    )
    def get(self, request):
        try:
            analysis_type = request.query_params.get('analysis_type')
            days = int(request.query_params.get('days', 30))
            tier = request.query_params.get('tier')
            
            if not analysis_type:
                return Response(
                    {"detail": "analysis_type 파라미터가 필요합니다."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            analyzer = SubscriptionAnalyzer()
            
            if analysis_type == 'conversion-funnel':
                result = analyzer.analyze_conversion_funnel(days)
            elif analysis_type == 'churn-patterns':
                result = analyzer.analyze_churn_patterns(days)
            elif analysis_type == 'customer-lifetime-value':
                result = analyzer.calculate_customer_lifetime_value(tier)
            elif analysis_type == 'insights-report':
                result = analyzer.generate_subscription_insights_report(days)
            else:
                return Response(
                    {"detail": "지원하지 않는 분석 유형입니다."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error in subscription analysis: {e}")
            return Response(
                {"detail": "구독 분석 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ConversionProbabilityView(APIView):
    """
    Predict conversion probability for a specific user (Admin only)
    """
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_summary="사용자 구독 전환 확률 예측",
        operation_description="""
        특정 사용자의 구독 전환 확률을 ML 기반 스코어링으로 예측합니다.
        
        **관리자 전용 기능**
        
        **예측 요소:**
        - 콘텐츠 생성 패턴 (30%)
        - 복습 활동 패턴 (25%)  
        - 연속 학습일 (20%)
        - 성공률 (15%)
        - 활동 최신성 (10%)
        """,
        manual_parameters=[
            openapi.Parameter('user_id', openapi.IN_QUERY, type=openapi.TYPE_INTEGER, 
                            required=True, description='대상 사용자 ID'),
        ],
        responses={
            200: "전환 확률 예측 결과",
            400: "잘못된 요청",
            401: "인증 필요", 
            403: "관리자 권한 필요"
        },
        tags=['Business Intelligence - Prediction']
    )
    def get(self, request):
        try:
            user_id = request.query_params.get('user_id')
            
            if not user_id:
                return Response(
                    {"detail": "user_id 파라미터가 필요합니다."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                user_id = int(user_id)
            except ValueError:
                return Response(
                    {"detail": "유효하지 않은 user_id입니다."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            analyzer = SubscriptionAnalyzer()
            result = analyzer.predict_conversion_probability(user_id)
            
            if 'error' in result:
                return Response(result, status=status.HTTP_404_NOT_FOUND)
            
            return Response(result)
            
        except Exception as e:
            logger.error(f"Error predicting conversion probability: {e}")
            return Response(
                {"detail": "전환 확률 예측 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )