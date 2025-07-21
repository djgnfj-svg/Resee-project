from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Count, Q, Avg, F, Case, When, IntegerField
from django.utils import timezone
from datetime import timedelta, datetime
from review.models import ReviewHistory, ReviewSchedule
from review.utils import calculate_success_rate, get_today_reviews_count, get_pending_reviews_count
from content.models import Content, Category
from collections import defaultdict


class DashboardView(APIView):
    """Dashboard analytics view"""
    
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
    """고급 학습 분석 데이터 제공"""
    
    def get(self, request):
        """종합적인 학습 분석 데이터 반환"""
        user = request.user
        
        return Response({
            'learning_insights': self._get_learning_insights(user),
            'category_performance': self._get_category_performance(user),
            'study_patterns': self._get_study_patterns(user),
            'achievement_stats': self._get_achievement_stats(user),
            'recommendations': self._get_recommendations(user),
        })
    
    def _get_learning_insights(self, user):
        """학습 인사이트 데이터"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        seven_days_ago = timezone.now() - timedelta(days=7)
        
        # 전체 통계
        total_content = user.contents.count()
        total_reviews = ReviewHistory.objects.filter(user=user).count()
        
        # 최근 30일 활동
        recent_reviews = ReviewHistory.objects.filter(
            user=user,
            review_date__gte=thirty_days_ago
        )
        
        # 최근 7일 활동
        week_reviews = ReviewHistory.objects.filter(
            user=user,
            review_date__gte=seven_days_ago
        )
        
        # 성공률 계산
        recent_success_rate = (
            recent_reviews.filter(result='remembered').count() / 
            recent_reviews.count() * 100
        ) if recent_reviews.count() > 0 else 0
        
        week_success_rate = (
            week_reviews.filter(result='remembered').count() / 
            week_reviews.count() * 100
        ) if week_reviews.count() > 0 else 0
        
        # 평균 복습 간격 계산
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
        """카테고리별 성과 분석"""
        categories = Category.objects.filter(user=user)
        category_stats = []
        
        for category in categories:
            # 카테고리별 콘텐츠 및 리뷰 통계
            content_count = Content.objects.filter(category=category).count()
            
            # 카테고리 콘텐츠의 모든 리뷰
            category_reviews = ReviewHistory.objects.filter(
                content__category=category
            )
            
            if category_reviews.exists():
                total_reviews = category_reviews.count()
                remembered_count = category_reviews.filter(result='remembered').count()
                success_rate = (remembered_count / total_reviews * 100)
                
                # 최근 30일 성과
                recent_reviews = category_reviews.filter(
                    review_date__gte=timezone.now() - timedelta(days=30)
                )
                recent_success_rate = (
                    recent_reviews.filter(result='remembered').count() / 
                    recent_reviews.count() * 100
                ) if recent_reviews.count() > 0 else 0
                
                # 난이도 계산 (실패율 기반)
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
        """학습 패턴 분석"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # 시간대별 학습 패턴
        hourly_pattern = defaultdict(int)
        reviews = ReviewHistory.objects.filter(
            user=user,
            review_date__gte=thirty_days_ago
        )
        
        for review in reviews:
            hour = review.review_date.hour
            hourly_pattern[hour] += 1
        
        # 요일별 학습 패턴
        daily_pattern = defaultdict(int)
        for review in reviews:
            weekday = review.review_date.weekday()  # 0=Monday, 6=Sunday
            daily_pattern[weekday] += 1
        
        # 패턴 데이터 정리
        hourly_data = [
            {'hour': hour, 'count': hourly_pattern[hour]}
            for hour in range(24)
        ]
        
        daily_labels = ['월', '화', '수', '목', '금', '토', '일']
        daily_data = [
            {'day': daily_labels[day], 'count': daily_pattern[day]}
            for day in range(7)
        ]
        
        # 최적 학습 시간 추천
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
        """성취 통계"""
        # 연속 학습일 계산
        current_streak = self._calculate_detailed_streak(user)
        max_streak = self._calculate_max_streak(user)
        
        # 완벽한 복습 세션 (모두 기억함)
        perfect_sessions = self._count_perfect_sessions(user)
        
        # 카테고리 마스터리 (성공률 90% 이상)
        mastered_categories = self._count_mastered_categories(user)
        
        # 월간 목표 달성률
        monthly_target = 100  # 기본 목표: 월 100회 복습
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
        """개인화된 학습 추천"""
        recommendations = []
        
        # 카테고리별 성과 분석
        category_performance = self._get_category_performance(user)
        
        # 약한 카테고리 추천
        weak_categories = [cat for cat in category_performance if cat['success_rate'] < 70]
        if weak_categories:
            recommendations.append({
                'type': 'weak_category',
                'title': '집중 학습 필요',
                'message': f"{weak_categories[0]['name']} 카테고리의 복습이 필요해 보여요.",
                'action': 'review_category',
                'category_id': weak_categories[0]['id'],
            })
        
        # 학습 패턴 기반 추천
        study_patterns = self._get_study_patterns(user)
        if study_patterns['total_study_sessions'] > 0:
            recommendations.append({
                'type': 'optimal_time',
                'title': '최적 학습 시간',
                'message': f"{study_patterns['recommended_hour']}시경이 가장 활발한 학습 시간대예요.",
                'action': 'schedule_reminder',
                'hour': study_patterns['recommended_hour'],
            })
        
        # 연속 학습일 격려
        achievement_stats = self._get_achievement_stats(user)
        if achievement_stats['current_streak'] >= 7:
            recommendations.append({
                'type': 'streak_celebration',
                'title': '연속 학습 달성!',
                'message': f"{achievement_stats['current_streak']}일 연속 학습 중이에요. 대단해요! 🎉",
                'action': 'continue_streak',
            })
        
        return recommendations
    
    def _calculate_average_interval(self, user):
        """평균 복습 간격 계산"""
        schedules = ReviewSchedule.objects.filter(user=user, interval__isnull=False)
        if schedules.exists():
            total_interval = sum(schedule.interval for schedule in schedules)
            return round(total_interval / schedules.count(), 1)
        return 0
    
    def _calculate_detailed_streak(self, user):
        """상세한 연속 학습일 계산"""
        today = timezone.now().date()
        streak = 0
        
        for i in range(365):  # 최대 1년
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
        """최대 연속 학습일 계산"""
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
        """완벽한 복습 세션 수 계산"""
        # 하루 단위로 모든 복습이 'remembered'인 날을 계산
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
        """마스터한 카테고리 수 (성공률 90% 이상)"""
        category_performance = self._get_category_performance(user)
        return len([cat for cat in category_performance if cat['success_rate'] >= 90])
    
    def _calculate_mastery_level(self, success_rate):
        """마스터리 레벨 계산"""
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


class LearningCalendarView(APIView):
    """학습 캘린더 및 히트맵 데이터"""
    
    def get(self, request):
        """캘린더 히트맵 데이터 반환"""
        user = request.user
        
        # 지난 365일 데이터
        one_year_ago = timezone.now().date() - timedelta(days=365)
        calendar_data = []
        
        for i in range(365):
            date = one_year_ago + timedelta(days=i)
            
            # 해당 날짜의 복습 데이터
            day_reviews = ReviewHistory.objects.filter(
                user=user,
                review_date__date=date
            )
            
            total_reviews = day_reviews.count()
            remembered_count = day_reviews.filter(result='remembered').count()
            success_rate = (remembered_count / total_reviews * 100) if total_reviews > 0 else 0
            
            # 강도 계산 (0-4 레벨)
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
        
        # 월별 요약 통계
        monthly_summary = self._get_monthly_summary(user, calendar_data)
        
        return Response({
            'calendar_data': calendar_data,
            'monthly_summary': monthly_summary,
            'total_active_days': len([d for d in calendar_data if d['count'] > 0]),
            'best_day': max(calendar_data, key=lambda x: x['count']) if calendar_data else None,
        })
    
    def _get_monthly_summary(self, user, calendar_data):
        """월별 요약 통계"""
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
        
        # 최근 12개월만 반환
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
        
        return result