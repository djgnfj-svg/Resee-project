from rest_framework import serializers
from .models import LegalDocument, UserConsent, DataDeletionRequest, DataExportRequest, CookieConsent


class LegalDocumentSerializer(serializers.ModelSerializer):
    """법적 문서 시리얼라이저"""
    
    class Meta:
        model = LegalDocument
        fields = [
            'id', 'title', 'document_type', 'content', 'version', 
            'effective_date', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class UserConsentSerializer(serializers.ModelSerializer):
    """사용자 동의 시리얼라이저"""
    
    class Meta:
        model = UserConsent
        fields = [
            'id', 'consent_type', 'document_version', 'is_consented', 
            'consented_at', 'ip_address', 'user_agent'
        ]
        read_only_fields = ['id', 'consented_at']


class CreateConsentSerializer(serializers.Serializer):
    """동의 생성 요청 시리얼라이저"""
    consent_type = serializers.ChoiceField(choices=UserConsent.ConsentType.choices)
    is_consented = serializers.BooleanField()
    document_version = serializers.CharField(max_length=20, required=False)
    
    def validate(self, data):
        # 필수 동의 항목 검증
        if data['consent_type'] in ['privacy_policy', 'terms_of_service']:
            if not data['is_consented']:
                raise serializers.ValidationError(
                    f"{data['consent_type']}는 필수 동의 항목입니다."
                )
        return data


class DataDeletionRequestSerializer(serializers.ModelSerializer):
    """데이터 삭제 요청 시리얼라이저"""
    
    class Meta:
        model = DataDeletionRequest
        fields = [
            'id', 'reason', 'status', 'processed_by', 'processed_at', 
            'admin_notes', 'requested_at'
        ]
        read_only_fields = [
            'id', 'status', 'processed_by', 'processed_at', 
            'admin_notes', 'requested_at'
        ]


class DataExportRequestSerializer(serializers.ModelSerializer):
    """데이터 내보내기 요청 시리얼라이저"""
    
    class Meta:
        model = DataExportRequest
        fields = [
            'id', 'status', 'expires_at', 'requested_at', 
            'processed_at', 'downloaded_at'
        ]
        read_only_fields = [
            'id', 'status', 'expires_at', 'requested_at', 
            'processed_at', 'downloaded_at'
        ]


class CookieConsentSerializer(serializers.ModelSerializer):
    """쿠키 동의 시리얼라이저"""
    
    class Meta:
        model = CookieConsent
        fields = [
            'id', 'essential_cookies', 'analytics_cookies', 
            'marketing_cookies', 'functional_cookies', 'consented_at'
        ]
        read_only_fields = ['id', 'consented_at']


class UpdateCookieConsentSerializer(serializers.Serializer):
    """쿠키 동의 업데이트 시리얼라이저"""
    analytics_cookies = serializers.BooleanField(default=False)
    marketing_cookies = serializers.BooleanField(default=False)
    functional_cookies = serializers.BooleanField(default=False)


class GDPRDataExportSerializer(serializers.Serializer):
    """GDPR 데이터 내보내기 응답 시리얼라이저"""
    user_data = serializers.DictField()
    export_date = serializers.DateTimeField()
    data_categories = serializers.ListField(child=serializers.CharField())
    
    def to_representation(self, instance):
        """사용자 데이터를 GDPR 준수 형태로 변환"""
        user = instance
        
        # 기본 사용자 정보
        user_data = {
            'personal_information': {
                'email': user.email,
                'username': user.username,
                'date_joined': user.date_joined.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'is_email_verified': user.is_email_verified,
                'weekly_goal': user.weekly_goal,
            },
            'subscription_information': {},
            'content_data': [],
            'review_history': [],
            'ai_usage': [],
            'payment_history': [],
            'consent_history': []
        }
        
        # 구독 정보
        if hasattr(user, 'subscription_payment'):
            subscription = user.subscription_payment
            user_data['subscription_information'] = {
                'plan': subscription.plan.name,
                'tier': subscription.plan.tier,
                'billing_cycle': subscription.billing_cycle,
                'is_active': subscription.is_active,
                'created_at': subscription.created_at.isoformat(),
                'current_period_end': subscription.current_period_end.isoformat()
            }
        
        # 콘텐츠 데이터
        user_data['content_data'] = [
            {
                'title': content.title,
                'category': content.category,
                'priority': content.priority,
                'content_type': content.content_type,
                'created_at': content.created_at.isoformat(),
                'updated_at': content.updated_at.isoformat()
            }
            for content in user.contents.all()
        ]
        
        # 복습 기록
        user_data['review_history'] = [
            {
                'content_title': history.content.title,
                'result': history.result,
                'time_spent': history.time_spent,
                'completed_at': history.completed_at.isoformat()
            }
            for history in user.review_histories.all()
        ]
        
        # AI 사용 기록
        if hasattr(user, 'ai_usage_records'):
            user_data['ai_usage'] = [
                {
                    'feature_type': record.feature_type,
                    'usage_count': record.usage_count,
                    'date': record.date.isoformat()
                }
                for record in user.ai_usage_records.all()
            ]
        
        # 결제 기록
        if hasattr(user, 'payments'):
            user_data['payment_history'] = [
                {
                    'amount': str(payment.amount),
                    'currency': payment.currency,
                    'status': payment.status,
                    'billing_cycle': payment.billing_cycle,
                    'created_at': payment.created_at.isoformat(),
                    'paid_at': payment.paid_at.isoformat() if payment.paid_at else None
                }
                for payment in user.payments.all()
            ]
        
        # 동의 기록
        user_data['consent_history'] = [
            {
                'consent_type': consent.consent_type,
                'document_version': consent.document_version,
                'is_consented': consent.is_consented,
                'consented_at': consent.consented_at.isoformat()
            }
            for consent in user.consents.all()
        ]
        
        return {
            'user_data': user_data,
            'export_date': user.date_joined,
            'data_categories': [
                'personal_information',
                'subscription_information', 
                'content_data',
                'review_history',
                'ai_usage',
                'payment_history',
                'consent_history'
            ]
        }