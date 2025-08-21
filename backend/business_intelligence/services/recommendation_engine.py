"""
AI-powered recommendation engine for learning optimization
"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from django.utils import timezone
from django.db.models import Avg, Count, Q

from review.models import ReviewHistory, ReviewSchedule
from content.models import Content
from .analytics_engine import LearningAnalyticsEngine

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """
    Generate personalized learning recommendations based on user patterns
    """
    
    def __init__(self, user):
        self.user = user
        self.analytics_engine = LearningAnalyticsEngine(user)
    
    def generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate comprehensive learning recommendations"""
        recommendations = []
        
        # Get user's learning insights
        insights = self.analytics_engine.get_learning_insights(30)
        content_analytics = self.analytics_engine.get_content_analytics()
        
        # Schedule optimization recommendations
        schedule_recs = self._generate_schedule_recommendations(insights)
        recommendations.extend(schedule_recs)
        
        # Content recommendations
        content_recs = self._generate_content_recommendations(content_analytics)
        recommendations.extend(content_recs)
        
        # Difficulty adjustment recommendations
        difficulty_recs = self._generate_difficulty_recommendations()
        recommendations.extend(difficulty_recs)
        
        # Engagement improvement recommendations
        engagement_recs = self._generate_engagement_recommendations(insights)
        recommendations.extend(engagement_recs)
        
        # Sort by priority and confidence score
        recommendations.sort(key=lambda x: (
            {'high': 3, 'medium': 2, 'low': 1}[x['priority']],
            x['confidence_score']
        ), reverse=True)
        
        return recommendations[:10]  # Return top 10 recommendations
    
    def _generate_schedule_recommendations(self, insights: Dict) -> List[Dict]:
        """Generate schedule optimization recommendations"""
        recommendations = []
        
        # Low consistency recommendation
        if insights['learning_consistency_score'] < 50:
            recommendations.append({
                'recommendation_type': 'schedule',
                'title': '학습 일관성 개선',
                'description': f"현재 일관성 점수가 {insights['learning_consistency_score']:.1f}%입니다. 매일 조금씩이라도 꾸준히 학습하면 기억 효과가 크게 향상됩니다.",
                'confidence_score': 0.9,
                'expected_improvement': '기억 유지율 20-30% 향상 예상',
                'action_items': [
                    '매일 최소 5분씩 복습하기',
                    '알림 설정으로 학습 시간 리마인더 활용',
                    '작은 목표부터 시작하여 점진적으로 늘리기'
                ],
                'priority': 'high'
            })
        
        # Optimal time recommendation
        if insights['most_productive_hour'] and insights['total_learning_days'] > 7:
            recommendations.append({
                'recommendation_type': 'schedule',
                'title': '최적 학습 시간 활용',
                'description': f"분석 결과 {insights['most_productive_hour']}시가 가장 생산적인 학습 시간입니다. 이 시간대를 적극 활용해보세요.",
                'confidence_score': 0.8,
                'expected_improvement': '학습 효율 15-25% 향상',
                'action_items': [
                    f'{insights["most_productive_hour"]}시경 주요 복습 진행',
                    '집중도가 높은 시간에 어려운 내용 학습',
                    '생체 리듬에 맞는 학습 계획 수립'
                ],
                'priority': 'medium'
            })
        
        # Review frequency optimization
        avg_reviews = insights['average_daily_reviews']
        if avg_reviews < 3:
            recommendations.append({
                'recommendation_type': 'schedule',
                'title': '복습 횟수 증가 필요',
                'description': f"현재 일평균 {avg_reviews:.1f}개 복습 중입니다. 조금 더 늘리면 학습 효과가 크게 향상됩니다.",
                'confidence_score': 0.85,
                'expected_improvement': '기억 정착률 40% 향상',
                'action_items': [
                    '일일 목표를 5-7개 복습으로 설정',
                    '짧은 시간 여러 번 나누어 복습',
                    '이동 시간 활용한 간단 복습'
                ],
                'priority': 'high'
            })
        elif avg_reviews > 20:
            recommendations.append({
                'recommendation_type': 'schedule',
                'title': '복습 부담 조절',
                'description': f"일평균 {avg_reviews:.1f}개로 너무 많은 복습을 하고 계십니다. 적절한 조절이 필요합니다.",
                'confidence_score': 0.8,
                'expected_improvement': '학습 지속성 및 집중도 향상',
                'action_items': [
                    '일일 복습량을 10-15개로 조정',
                    '질보다 양에 치우치지 않도록 주의',
                    '휴식 시간 확보로 학습 효율성 증대'
                ],
                'priority': 'medium'
            })
        
        return recommendations
    
    def _generate_content_recommendations(self, content_analytics: Dict) -> List[Dict]:
        """Generate content-related recommendations"""
        recommendations = []
        
        # Struggling content help
        struggling_count = content_analytics['struggling_content']
        if struggling_count > 0:
            recommendations.append({
                'recommendation_type': 'content',
                'title': '어려운 콘텐츠 집중 관리',
                'description': f"현재 {struggling_count}개의 콘텐츠에서 어려움을 겪고 있습니다. 이들을 우선적으로 관리해보세요.",
                'confidence_score': 0.9,
                'expected_improvement': '전체 성공률 10-20% 향상',
                'action_items': [
                    '어려운 내용을 더 작은 단위로 나누기',
                    '다양한 각도에서 접근해보기',
                    'AI 질문 생성으로 이해도 점검'
                ],
                'priority': 'high'
            })
        
        # Abandoned content recovery
        abandoned_count = content_analytics['abandoned_content']
        if abandoned_count > 0:
            recommendations.append({
                'recommendation_type': 'content',
                'title': '방치된 콘텐츠 재활용',
                'description': f"{abandoned_count}개의 콘텐츠가 복습되지 않고 있습니다. 다시 학습 계획에 포함시켜보세요.",
                'confidence_score': 0.7,
                'expected_improvement': '학습 자산 활용도 증대',
                'action_items': [
                    '오래된 콘텐츠부터 다시 검토',
                    '현재 관심사와 연결점 찾기',
                    '불필요한 콘텐츠는 정리하기'
                ],
                'priority': 'low'
            })
        
        # Content type optimization
        most_effective = content_analytics['most_effective_content_type']
        least_effective = content_analytics['least_effective_content_type']
        
        if most_effective != 'N/A' and least_effective != 'N/A' and most_effective != least_effective:
            recommendations.append({
                'recommendation_type': 'content',
                'title': '효과적인 콘텐츠 유형 활용',
                'description': f"{most_effective} 유형의 학습 효과가 가장 좋고, {least_effective} 유형이 상대적으로 어려워 보입니다.",
                'confidence_score': 0.8,
                'expected_improvement': '콘텐츠 유형별 맞춤 전략 수립',
                'action_items': [
                    f'{most_effective} 형태로 더 많은 콘텐츠 생성',
                    f'{least_effective} 콘텐츠는 더 세분화하여 접근',
                    '개인 학습 스타일에 맞는 콘텐츠 형태 개발'
                ],
                'priority': 'medium'
            })
        
        return recommendations
    
    def _generate_difficulty_recommendations(self) -> List[Dict]:
        """Generate difficulty adjustment recommendations"""
        recommendations = []
        
        # Analyze recent success rates by difficulty
        recent_reviews = ReviewHistory.objects.filter(
            user=self.user,
            review_date__gte=timezone.now() - timedelta(days=7)
        ).select_related('content')
        
        if recent_reviews.exists():
            # Group by difficulty and calculate success rates
            difficulty_stats = {}
            for review in recent_reviews:
                difficulty = getattr(review.content, 'difficulty_level', 3)
                if difficulty not in difficulty_stats:
                    difficulty_stats[difficulty] = {'total': 0, 'success': 0}
                
                difficulty_stats[difficulty]['total'] += 1
                if review.result == 'remembered':
                    difficulty_stats[difficulty]['success'] += 1
            
            # Find problematic difficulty levels
            for difficulty, stats in difficulty_stats.items():
                if stats['total'] >= 3:  # Only consider if enough samples
                    success_rate = (stats['success'] / stats['total']) * 100
                    
                    if success_rate < 40:  # Very low success rate
                        recommendations.append({
                            'recommendation_type': 'difficulty',
                            'title': f'난이도 {difficulty} 콘텐츠 조정 필요',
                            'description': f"난이도 {difficulty} 콘텐츠의 성공률이 {success_rate:.1f}%로 낮습니다. 접근 방식을 바꿔보세요.",
                            'confidence_score': 0.8,
                            'expected_improvement': '해당 난이도 성공률 20-30% 향상',
                            'action_items': [
                                '더 쉬운 단계부터 시작하여 점진적 접근',
                                '개념 이해를 위한 추가 학습 자료 활용',
                                '반복 학습 횟수 늘리기'
                            ],
                            'priority': 'high'
                        })
                    elif success_rate > 90:  # Very high success rate
                        recommendations.append({
                            'recommendation_type': 'difficulty',
                            'title': f'난이도 {difficulty} 콘텐츠 레벨업',
                            'description': f"난이도 {difficulty} 콘텐츠의 성공률이 {success_rate:.1f}%로 매우 높습니다. 더 도전적인 내용을 시도해보세요.",
                            'confidence_score': 0.75,
                            'expected_improvement': '학습 효율성 및 성장 속도 향상',
                            'action_items': [
                                '더 높은 난이도의 콘텐츠 추가',
                                '심화 학습 내용 포함',
                                '응용 문제나 실제 사례 적용'
                            ],
                            'priority': 'medium'
                        })
        
        return recommendations
    
    def _generate_engagement_recommendations(self, insights: Dict) -> List[Dict]:
        """Generate engagement improvement recommendations"""
        recommendations = []
        
        # Low success rate
        success_rate = insights['average_success_rate']
        if success_rate < 60:
            recommendations.append({
                'recommendation_type': 'engagement',
                'title': '학습 성공률 개선',
                'description': f"현재 성공률이 {success_rate:.1f}%입니다. 학습 방법과 복습 주기를 조정해보세요.",
                'confidence_score': 0.85,
                'expected_improvement': '성공률 20-30% 향상',
                'action_items': [
                    '복습 간격을 더 짧게 조정',
                    '이해하기 쉬운 형태로 콘텐츠 재구성',
                    'AI 질문으로 이해도 사전 점검'
                ],
                'priority': 'high'
            })
        
        # Short study sessions
        total_hours = insights['total_study_hours']
        learning_days = insights['total_learning_days']
        if learning_days > 0:
            avg_daily_hours = total_hours / learning_days
            if avg_daily_hours < 0.5:  # Less than 30 minutes per day
                recommendations.append({
                    'recommendation_type': 'engagement',
                    'title': '학습 시간 확대',
                    'description': f"일평균 {avg_daily_hours*60:.1f}분 학습 중입니다. 조금 더 시간을 투자하면 효과가 배가될 것입니다.",
                    'confidence_score': 0.8,
                    'expected_improvement': '학습 깊이 및 정착률 향상',
                    'action_items': [
                        '일일 학습 시간을 45분~1시간으로 확대',
                        '집중 학습 세션과 가벼운 복습 세션 구분',
                        '학습 환경 최적화로 효율성 증대'
                    ],
                    'priority': 'medium'
                })
        
        # Streak breaking
        current_streak = insights['current_streak']
        if current_streak == 0 and insights['total_learning_days'] > 0:
            recommendations.append({
                'recommendation_type': 'engagement',
                'title': '학습 연속성 회복',
                'description': "학습 연속 기록이 끊어졌습니다. 다시 꾸준한 학습 습관을 만들어보세요.",
                'confidence_score': 0.9,
                'expected_improvement': '학습 동기 및 지속성 향상',
                'action_items': [
                    '오늘부터 새로운 연속 기록 시작',
                    '하루 최소 1개라도 복습하기',
                    '학습 알림 및 리마인더 설정'
                ],
                'priority': 'high'
            })
        
        return recommendations