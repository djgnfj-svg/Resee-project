import json
import os
import tempfile
from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class GDPRService:
    """GDPR 관련 서비스"""
    
    @staticmethod
    def export_user_data(user):
        """사용자 데이터를 JSON 형태로 내보내기"""
        data = {
            'export_info': {
                'export_date': timezone.now().isoformat(),
                'user_id': user.id,
                'export_format': 'JSON',
                'gdpr_compliant': True
            },
            'personal_information': {
                'email': user.email,
                'username': user.username or '',
                'date_joined': user.date_joined.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'is_email_verified': user.is_email_verified,
                'weekly_goal': user.weekly_goal,
                'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None,
                'updated_at': user.updated_at.isoformat() if hasattr(user, 'updated_at') and user.updated_at else None
            },
            'subscription_information': GDPRService._get_subscription_data(user),
            'content_data': GDPRService._get_content_data(user),
            'review_history': GDPRService._get_review_data(user),
            'ai_usage_history': GDPRService._get_ai_usage_data(user),
            'payment_history': GDPRService._get_payment_data(user),
            'consent_history': GDPRService._get_consent_data(user),
            'technical_data': GDPRService._get_technical_data(user)
        }
        
        return data
    
    @staticmethod
    def _get_subscription_data(user):
        """구독 정보 수집"""
        if not hasattr(user, 'subscription_payment'):
            return None
        
        subscription = user.subscription_payment
        return {
            'plan_name': subscription.plan.name,
            'plan_tier': subscription.plan.tier,
            'billing_cycle': subscription.billing_cycle,
            'is_active': subscription.is_active,
            'current_period_start': subscription.current_period_start.isoformat(),
            'current_period_end': subscription.current_period_end.isoformat(),
            'trial_end': subscription.trial_end.isoformat() if subscription.trial_end else None,
            'canceled_at': subscription.canceled_at.isoformat() if subscription.canceled_at else None,
            'created_at': subscription.created_at.isoformat(),
            'updated_at': subscription.updated_at.isoformat()
        }
    
    @staticmethod
    def _get_content_data(user):
        """콘텐츠 데이터 수집"""
        contents = []
        for content in user.contents.all():
            content_data = {
                'id': content.id,
                'title': content.title,
                'category': content.category,
                'priority': content.priority,
                'content_type': content.content_type,
                'tags': content.tags,
                'created_at': content.created_at.isoformat(),
                'updated_at': content.updated_at.isoformat()
            }
            
            # 콘텐츠 내용은 개인정보 보호를 위해 제외하거나 요약만 포함
            if hasattr(content, 'body'):
                content_data['content_length'] = len(content.body) if content.body else 0
                content_data['has_content'] = bool(content.body)
            
            contents.append(content_data)
        
        return contents
    
    @staticmethod
    def _get_review_data(user):
        """복습 기록 수집"""
        reviews = []
        for review in user.review_histories.all():
            reviews.append({
                'content_id': review.content.id,
                'content_title': review.content.title,
                'result': review.result,
                'time_spent': review.time_spent,
                'completed_at': review.completed_at.isoformat(),
                'created_at': review.created_at.isoformat() if hasattr(review, 'created_at') else None
            })
        
        return reviews
    
    @staticmethod
    def _get_ai_usage_data(user):
        """AI 사용 기록 수집"""
        if not hasattr(user, 'ai_usage_records'):
            return []
        
        usage_records = []
        for record in user.ai_usage_records.all():
            usage_records.append({
                'feature_type': record.feature_type,
                'usage_count': record.usage_count,
                'date': record.date.isoformat(),
                'created_at': record.created_at.isoformat() if hasattr(record, 'created_at') else None
            })
        
        return usage_records
    
    @staticmethod
    def _get_payment_data(user):
        """결제 기록 수집"""
        if not hasattr(user, 'payments'):
            return []
        
        payments = []
        for payment in user.payments.all():
            # 결제 정보는 민감하므로 최소한의 정보만 포함
            payments.append({
                'id': payment.id,
                'plan_name': payment.plan.name,
                'amount': str(payment.amount),
                'currency': payment.currency,
                'billing_cycle': payment.billing_cycle,
                'status': payment.status,
                'created_at': payment.created_at.isoformat(),
                'paid_at': payment.paid_at.isoformat() if payment.paid_at else None
                # Stripe 관련 정보는 보안상 제외
            })
        
        return payments
    
    @staticmethod
    def _get_consent_data(user):
        """동의 기록 수집"""
        consents = []
        for consent in user.consents.all():
            consents.append({
                'consent_type': consent.consent_type,
                'document_version': consent.document_version,
                'is_consented': consent.is_consented,
                'consented_at': consent.consented_at.isoformat(),
                'ip_address': consent.ip_address,
                'user_agent': consent.user_agent[:100] if consent.user_agent else None  # 일부만 포함
            })
        
        return consents
    
    @staticmethod
    def _get_technical_data(user):
        """기술적 데이터 수집"""
        technical_data = {
            'login_history': {
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'date_joined': user.date_joined.isoformat()
            }
        }
        
        # 쿠키 동의 기록
        if hasattr(user, 'cookie_consents'):
            cookie_consents = []
            for consent in user.cookie_consents.all():
                cookie_consents.append({
                    'essential_cookies': consent.essential_cookies,
                    'analytics_cookies': consent.analytics_cookies,
                    'marketing_cookies': consent.marketing_cookies,
                    'functional_cookies': consent.functional_cookies,
                    'consented_at': consent.consented_at.isoformat()
                })
            technical_data['cookie_consents'] = cookie_consents
        
        return technical_data
    
    @staticmethod
    def create_export_file(user):
        """사용자 데이터를 파일로 생성"""
        data = GDPRService.export_user_data(user)
        
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(
            mode='w', 
            suffix='.json', 
            delete=False,
            encoding='utf-8'
        ) as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            file_path = f.name
        
        return file_path
    
    @staticmethod
    def delete_user_data(user, keep_legal_records=True):
        """사용자 데이터 삭제 (GDPR Right to be Forgotten)"""
        deletion_log = {
            'user_id': user.id,
            'email': user.email,
            'deletion_date': timezone.now().isoformat(),
            'deleted_data': []
        }
        
        # 1. 콘텐츠 데이터 삭제
        content_count = user.contents.count()
        user.contents.all().delete()
        deletion_log['deleted_data'].append(f'Contents: {content_count}')
        
        # 2. 복습 기록 삭제
        review_count = user.review_histories.count()
        user.review_histories.all().delete()
        deletion_log['deleted_data'].append(f'Review histories: {review_count}')
        
        # 3. AI 사용 기록 삭제
        if hasattr(user, 'ai_usage_records'):
            ai_count = user.ai_usage_records.count()
            user.ai_usage_records.all().delete()
            deletion_log['deleted_data'].append(f'AI usage records: {ai_count}')
        
        # 4. 결제 기록 (법적 요구사항에 따라 보관 또는 삭제)
        if not keep_legal_records and hasattr(user, 'payments'):
            payment_count = user.payments.count()
            user.payments.all().delete()
            deletion_log['deleted_data'].append(f'Payment records: {payment_count}')
        
        # 5. 구독 정보 삭제 (결제 기록과 연결되므로 주의)
        if hasattr(user, 'subscription_payment'):
            user.subscription_payment.delete()
            deletion_log['deleted_data'].append('Subscription information')
        
        # 6. 개인정보 익명화
        user.email = f'deleted_user_{user.id}@deleted.resee.com'
        user.username = f'deleted_user_{user.id}'
        user.first_name = ''
        user.last_name = ''
        user.is_active = False
        user.save()
        
        # 7. 동의 기록은 법적 요구사항에 따라 보관
        if keep_legal_records:
            deletion_log['retained_data'] = ['Consent records (legal requirement)']
        else:
            consent_count = user.consents.count()
            user.consents.all().delete()
            deletion_log['deleted_data'].append(f'Consent records: {consent_count}')
        
        return deletion_log
    
    @staticmethod
    def anonymize_user_data(user):
        """사용자 데이터 익명화 (삭제 대신 익명화가 적절한 경우)"""
        anonymization_log = {
            'user_id': user.id,
            'anonymization_date': timezone.now().isoformat(),
            'anonymized_fields': []
        }
        
        # 개인 식별 정보 익명화
        original_email = user.email
        user.email = f'anonymous_user_{user.id}@anonymous.resee.com'
        user.username = f'anonymous_user_{user.id}'
        user.first_name = ''
        user.last_name = ''
        
        anonymization_log['anonymized_fields'] = [
            'email', 'username', 'first_name', 'last_name'
        ]
        anonymization_log['original_email_hash'] = hash(original_email)
        
        user.save()
        
        return anonymization_log