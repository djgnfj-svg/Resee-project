from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional
from django.db.models import Q, Count, Avg, Sum, F
from django.contrib.auth import get_user_model
from accounts.models import Subscription
from content.models import Content
from review.models import ReviewHistory
from ..models import SubscriptionAnalytics

User = get_user_model()

class SubscriptionAnalyzer:
    """
    Advanced subscription analytics and conversion analysis
    """
    
    def __init__(self):
        self.user_model = User
    
    def analyze_conversion_funnel(self, days: int = 30) -> Dict[str, Any]:
        """분석 전환 깔대기 분석"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Stage 1: 회원가입한 사용자
        total_signups = self.user_model.objects.filter(
            date_joined__date__gte=start_date,
            date_joined__date__lte=end_date
        ).count()
        
        # Stage 2: 콘텐츠를 생성한 사용자
        users_with_content = self.user_model.objects.filter(
            date_joined__date__gte=start_date,
            date_joined__date__lte=end_date,
            contents__isnull=False
        ).distinct().count()
        
        # Stage 3: 복습을 시작한 사용자
        users_with_reviews = self.user_model.objects.filter(
            date_joined__date__gte=start_date,
            date_joined__date__lte=end_date,
            review_histories__isnull=False
        ).distinct().count()
        
        # Stage 4: 구독한 사용자
        converted_users = self.user_model.objects.filter(
            date_joined__date__gte=start_date,
            date_joined__date__lte=end_date,
            subscription__tier__in=['BASIC', 'PRO']
        ).distinct().count()
        
        # 전환율 계산
        content_conversion_rate = (users_with_content / total_signups * 100) if total_signups > 0 else 0
        review_conversion_rate = (users_with_reviews / users_with_content * 100) if users_with_content > 0 else 0
        subscription_conversion_rate = (converted_users / users_with_reviews * 100) if users_with_reviews > 0 else 0
        overall_conversion_rate = (converted_users / total_signups * 100) if total_signups > 0 else 0
        
        return {
            'period_days': days,
            'funnel_data': {
                'total_signups': total_signups,
                'users_with_content': users_with_content,
                'users_with_reviews': users_with_reviews,
                'converted_users': converted_users
            },
            'conversion_rates': {
                'signup_to_content': round(content_conversion_rate, 2),
                'content_to_review': round(review_conversion_rate, 2),
                'review_to_subscription': round(subscription_conversion_rate, 2),
                'overall_conversion': round(overall_conversion_rate, 2)
            },
            'insights': self._generate_funnel_insights(
                total_signups, users_with_content, users_with_reviews, converted_users
            )
        }
    
    def analyze_churn_patterns(self, days: int = 90) -> Dict[str, Any]:
        """이탈 패턴 분석"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # 구독 취소한 사용자
        churned_subscriptions = Subscription.objects.filter(
            updated_at__date__gte=start_date,
            tier='FREE'
        ).exclude(
            created_at__date__gte=start_date  # 신규 무료 사용자 제외
        )
        
        churn_analysis = []
        total_churned = churned_subscriptions.count()
        
        for subscription in churned_subscriptions:
            user = subscription.user
            
            # 구독 기간 계산
            subscription_duration = (subscription.updated_at.date() - subscription.created_at.date()).days
            
            # 마지막 활동 분석
            last_content = Content.objects.filter(user=user).order_by('-created_at').first()
            last_review = ReviewHistory.objects.filter(user=user).order_by('-reviewed_at').first()
            
            last_activity = None
            if last_content and last_review:
                last_activity = max(last_content.created_at, last_review.reviewed_at)
            elif last_content:
                last_activity = last_content.created_at
            elif last_review:
                last_activity = last_review.reviewed_at
            
            # 이탈 전 사용 패턴
            pre_churn_reviews = ReviewHistory.objects.filter(
                user=user,
                reviewed_at__date__gte=subscription.updated_at.date() - timedelta(days=7),
                reviewed_at__date__lt=subscription.updated_at.date()
            ).count()
            
            churn_analysis.append({
                'user_id': user.id,
                'subscription_duration_days': subscription_duration,
                'days_since_last_activity': (end_date - last_activity.date()).days if last_activity else None,
                'pre_churn_reviews': pre_churn_reviews,
                'total_contents': user.contents.count(),
                'total_reviews': user.review_histories.count()
            })
        
        # 이탈 패턴 인사이트
        if churn_analysis:
            avg_duration = sum(c['subscription_duration_days'] for c in churn_analysis) / len(churn_analysis)
            avg_last_activity = sum(c['days_since_last_activity'] for c in churn_analysis if c['days_since_last_activity']) / len([c for c in churn_analysis if c['days_since_last_activity']])
            
            high_risk_indicators = []
            if avg_last_activity > 7:
                high_risk_indicators.append("7일 이상 비활성 상태")
            if avg_duration < 30:
                high_risk_indicators.append("구독 후 30일 이내 이탈")
        else:
            avg_duration = 0
            avg_last_activity = 0
            high_risk_indicators = []
        
        return {
            'period_days': days,
            'total_churned_users': total_churned,
            'average_subscription_duration': round(avg_duration, 1),
            'average_days_since_last_activity': round(avg_last_activity, 1),
            'high_risk_indicators': high_risk_indicators,
            'detailed_analysis': churn_analysis[:10],  # Top 10 for detailed view
            'recommendations': self._generate_retention_recommendations(churn_analysis)
        }
    
    def calculate_customer_lifetime_value(self, tier: str = None) -> Dict[str, Any]:
        """고객 생애 가치 (CLV) 계산"""
        query = Subscription.objects.exclude(tier='FREE')
        if tier:
            query = query.filter(tier=tier)
        
        # 월별 수익 계산
        tier_pricing = {
            'BASIC': Decimal('9900'),
            'PRO': Decimal('19900')
        }
        
        clv_data = []
        active_subscriptions = query.filter(tier__in=['BASIC', 'PRO'])
        
        for subscription in active_subscriptions:
            user = subscription.user
            subscription_start = subscription.created_at.date()
            subscription_days = (datetime.now().date() - subscription_start).days
            subscription_months = max(1, subscription_days / 30)
            
            # 구독 기간 기반 실제 수익 계산
            total_payments = subscription.amount_paid or Decimal('0')
            
            # 예상 월 수익
            monthly_revenue = tier_pricing.get(subscription.tier, Decimal('0'))
            
            # 사용 패턴 기반 가치 점수
            engagement_score = self._calculate_engagement_score(user)
            
            clv_data.append({
                'user_id': user.id,
                'tier': subscription.tier,
                'subscription_months': round(subscription_months, 1),
                'total_payments': float(total_payments),
                'monthly_revenue': float(monthly_revenue),
                'estimated_clv': float(total_payments + (monthly_revenue * engagement_score)),
                'engagement_score': engagement_score
            })
        
        # CLV 통계
        if clv_data:
            avg_clv = sum(c['estimated_clv'] for c in clv_data) / len(clv_data)
            total_clv = sum(c['estimated_clv'] for c in clv_data)
            
            # 티어별 CLV
            tier_clv = {}
            for tier_name in ['BASIC', 'PRO']:
                tier_data = [c for c in clv_data if c['tier'] == tier_name]
                if tier_data:
                    tier_clv[tier_name] = {
                        'count': len(tier_data),
                        'average_clv': sum(c['estimated_clv'] for c in tier_data) / len(tier_data),
                        'total_clv': sum(c['estimated_clv'] for c in tier_data)
                    }
        else:
            avg_clv = 0
            total_clv = 0
            tier_clv = {}
        
        return {
            'total_active_subscriptions': len(clv_data),
            'average_clv': round(avg_clv, 0),
            'total_clv': round(total_clv, 0),
            'tier_breakdown': tier_clv,
            'top_customers': sorted(clv_data, key=lambda x: x['estimated_clv'], reverse=True)[:10]
        }
    
    def predict_conversion_probability(self, user_id: int) -> Dict[str, Any]:
        """사용자 구독 전환 확률 예측 (ML 기반 스코어링)"""
        try:
            user = self.user_model.objects.get(id=user_id)
        except self.user_model.DoesNotExist:
            return {'error': 'User not found'}
        
        if user.subscription.tier != 'FREE':
            return {'message': 'User is already subscribed', 'current_tier': user.subscription.tier}
        
        # 특성 추출
        features = self._extract_user_features(user)
        
        # 규칙 기반 스코어링 (간단한 ML 알고리즘 모방)
        conversion_score = 0
        score_breakdown = {}
        
        # 콘텐츠 생성 패턴 (30%)
        content_score = min(features['total_contents'] * 5, 30)
        conversion_score += content_score
        score_breakdown['content_creation'] = content_score
        
        # 복습 활동 패턴 (25%)
        review_score = min(features['total_reviews'] * 3, 25)
        conversion_score += review_score
        score_breakdown['review_activity'] = review_score
        
        # 연속 학습일 (20%)
        streak_score = min(features['longest_streak'] * 2, 20)
        conversion_score += streak_score
        score_breakdown['learning_streak'] = streak_score
        
        # 성공률 (15%)
        success_score = features['avg_success_rate'] * 0.15
        conversion_score += success_score
        score_breakdown['success_rate'] = round(success_score, 1)
        
        # 활동 최신성 (10%)
        if features['days_since_last_activity'] <= 1:
            recency_score = 10
        elif features['days_since_last_activity'] <= 7:
            recency_score = 7
        elif features['days_since_last_activity'] <= 30:
            recency_score = 3
        else:
            recency_score = 0
        conversion_score += recency_score
        score_breakdown['recent_activity'] = recency_score
        
        # 확률 계산 (시그모이드 함수 근사)
        probability = min(100, max(0, conversion_score))
        
        # 추천 행동
        recommendations = self._generate_conversion_recommendations(features, probability)
        
        return {
            'user_id': user_id,
            'conversion_probability': round(probability, 1),
            'score_breakdown': score_breakdown,
            'user_features': features,
            'recommendations': recommendations,
            'risk_level': 'high' if probability >= 70 else 'medium' if probability >= 40 else 'low'
        }
    
    def _extract_user_features(self, user) -> Dict[str, Any]:
        """사용자 특성 추출"""
        # 기본 통계
        total_contents = user.contents.count()
        total_reviews = user.review_histories.count()
        
        # 성공률 계산
        successful_reviews = user.review_histories.filter(result='remembered').count()
        avg_success_rate = (successful_reviews / total_reviews * 100) if total_reviews > 0 else 0
        
        # 연속 학습일 계산
        review_dates = user.review_histories.values_list('reviewed_at__date', flat=True).distinct().order_by('reviewed_at__date')
        longest_streak = self._calculate_longest_streak(list(review_dates))
        
        # 최근 활동
        last_activity = max(
            user.contents.aggregate(max_date=F('created_at'))['max_date'] or datetime.min.replace(tzinfo=None),
            user.review_histories.aggregate(max_date=F('reviewed_at'))['max_date'] or datetime.min.replace(tzinfo=None)
        )
        days_since_last_activity = (datetime.now().replace(tzinfo=None) - last_activity.replace(tzinfo=None)).days
        
        # 가입 후 경과일
        days_since_signup = (datetime.now().date() - user.date_joined.date()).days
        
        return {
            'total_contents': total_contents,
            'total_reviews': total_reviews,
            'avg_success_rate': round(avg_success_rate, 1),
            'longest_streak': longest_streak,
            'days_since_last_activity': days_since_last_activity,
            'days_since_signup': days_since_signup,
            'reviews_per_day': round(total_reviews / max(1, days_since_signup), 2)
        }
    
    def _calculate_longest_streak(self, dates: List) -> int:
        """최대 연속 학습일 계산"""
        if not dates:
            return 0
        
        longest = 1
        current = 1
        
        for i in range(1, len(dates)):
            if (dates[i] - dates[i-1]).days == 1:
                current += 1
                longest = max(longest, current)
            else:
                current = 1
        
        return longest
    
    def _calculate_engagement_score(self, user) -> float:
        """사용자 참여 점수 계산"""
        days_since_signup = (datetime.now().date() - user.date_joined.date()).days
        if days_since_signup == 0:
            return 1.0
        
        # 활동 빈도 기반 점수
        total_activities = user.contents.count() + user.review_histories.count()
        activity_score = min(2.0, total_activities / days_since_signup * 10)
        
        # 최근 활동 기반 점수
        recent_reviews = user.review_histories.filter(
            reviewed_at__date__gte=datetime.now().date() - timedelta(days=7)
        ).count()
        recency_score = min(1.5, recent_reviews * 0.3)
        
        return round(activity_score + recency_score, 2)
    
    def _generate_funnel_insights(self, signups, content_users, review_users, converted) -> List[str]:
        """전환 깔대기 인사이트 생성"""
        insights = []
        
        if signups > 0:
            content_rate = content_users / signups * 100
            if content_rate < 50:
                insights.append("신규 가입자의 콘텐츠 생성률이 낮습니다. 온보딩 프로세스 개선이 필요합니다.")
            
            if content_users > 0:
                review_rate = review_users / content_users * 100
                if review_rate < 70:
                    insights.append("콘텐츠 생성 후 복습 전환율이 낮습니다. 복습 알림 시스템 강화를 권장합니다.")
            
            if review_users > 0:
                subscription_rate = converted / review_users * 100
                if subscription_rate < 20:
                    insights.append("복습 사용자의 구독 전환율이 낮습니다. 프리미엄 기능의 가치 제안을 강화해야 합니다.")
        
        return insights
    
    def _generate_retention_recommendations(self, churn_data: List[Dict]) -> List[str]:
        """이탈 방지 추천사항 생성"""
        recommendations = []
        
        if not churn_data:
            return recommendations
        
        # 평균 구독 기간이 짧은 경우
        avg_duration = sum(c['subscription_duration_days'] for c in churn_data) / len(churn_data)
        if avg_duration < 30:
            recommendations.append("초기 구독자 온보딩 프로그램 강화")
            recommendations.append("첫 30일간 개인화된 학습 가이드 제공")
        
        # 비활성 사용자가 많은 경우
        inactive_users = len([c for c in churn_data if c['days_since_last_activity'] and c['days_since_last_activity'] > 7])
        if inactive_users > len(churn_data) * 0.5:
            recommendations.append("비활성 사용자 재참여 캠페인 실시")
            recommendations.append("맞춤형 복습 알림 시스템 도입")
        
        # 콘텐츠 생성이 적은 사용자가 많은 경우
        low_content_users = len([c for c in churn_data if c['total_contents'] < 10])
        if low_content_users > len(churn_data) * 0.7:
            recommendations.append("콘텐츠 생성 도구 개선 및 템플릿 제공")
        
        return recommendations
    
    def _generate_conversion_recommendations(self, features: Dict, probability: float) -> List[str]:
        """전환 확률 향상 추천사항"""
        recommendations = []
        
        if features['total_contents'] < 5:
            recommendations.append("더 많은 학습 콘텐츠 생성을 유도하는 가이드 제공")
        
        if features['total_reviews'] < 10:
            recommendations.append("복습의 중요성과 효과에 대한 교육 콘텐츠 제공")
        
        if features['avg_success_rate'] < 70:
            recommendations.append("학습 방법 개선을 위한 개인화된 팁 제공")
        
        if features['days_since_last_activity'] > 3:
            recommendations.append("개인화된 학습 리마인더 발송")
        
        if probability >= 70:
            recommendations.append("프리미엄 기능 체험판 제공")
            recommendations.append("할인 쿠폰을 통한 구독 유도")
        elif probability >= 40:
            recommendations.append("성공 사례와 혜택 중심의 마케팅 메시지")
            recommendations.append("무료 기능의 한계점 강조")
        else:
            recommendations.append("기본 기능 사용법 교육 우선")
            recommendations.append("학습 습관 형성 지원")
        
        return recommendations

    def generate_subscription_insights_report(self, days: int = 30) -> Dict[str, Any]:
        """종합 구독 인사이트 보고서 생성"""
        funnel_data = self.analyze_conversion_funnel(days)
        churn_data = self.analyze_churn_patterns(days * 3)  # 더 긴 기간으로 이탈 분석
        clv_data = self.calculate_customer_lifetime_value()
        
        return {
            'report_period': days,
            'generated_at': datetime.now().isoformat(),
            'conversion_funnel': funnel_data,
            'churn_analysis': churn_data,
            'customer_lifetime_value': clv_data,
            'summary': {
                'total_signups': funnel_data['funnel_data']['total_signups'],
                'conversion_rate': funnel_data['conversion_rates']['overall_conversion'],
                'churned_users': churn_data['total_churned_users'],
                'total_clv': clv_data['total_clv'],
                'avg_clv': clv_data['average_clv']
            },
            'action_items': [
                *funnel_data['insights'],
                *churn_data['recommendations']
            ]
        }