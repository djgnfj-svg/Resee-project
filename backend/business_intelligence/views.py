"""
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