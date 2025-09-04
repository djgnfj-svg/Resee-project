import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


@shared_task
def send_verification_email(user_id):
    """Send email verification to user"""
    try:
        from .models import User
        user = User.objects.get(id=user_id)
        
        if user.is_email_verified:
            logger.info(f"User {user.email} is already verified")
            return
        
        # Generate verification token
        token = user.generate_email_verification_token()
        
        # Create verification URL
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}&email={user.email}"
        
        # Render email template
        context = {
            'user': user,
            'verification_url': verification_url,
            'expiry_hours': settings.EMAIL_VERIFICATION_TIMEOUT_DAYS * 24,
        }
        
        html_message = render_to_string('accounts/email_verification.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject='[Resee] 이메일 인증을 완료해주세요',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Verification email sent to {user.email}")
        return True
        
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist")
        return False
    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")
        return False


@shared_task
def send_welcome_email(user_id):
    """Send welcome email after successful verification"""
    try:
        from .models import User
        user = User.objects.get(id=user_id)
        
        context = {
            'user': user,
            'login_url': f"{settings.FRONTEND_URL}/login",
        }
        
        html_message = render_to_string('accounts/welcome_email.html', context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject='[Resee] 환영합니다!',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Welcome email sent to {user.email}")
        return True
        
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist")
        return False
    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")
        return False


@shared_task
def check_and_process_subscription_renewals():
    """Check for subscriptions that need to be renewed and process them"""
    from datetime import timedelta
    from django.utils import timezone
    from .models import Subscription, PaymentHistory, SubscriptionTier
    
    try:
        now = timezone.now()
        
        # Find subscriptions that need renewal (expiring in next 24 hours and auto-renewal is on)
        upcoming_renewals = Subscription.objects.filter(
            is_active=True,
            auto_renewal=True,
            end_date__isnull=False,
            end_date__lte=now + timedelta(hours=24),
            end_date__gt=now
        ).exclude(tier=SubscriptionTier.FREE)
        
        renewed_count = 0
        failed_count = 0
        
        for subscription in upcoming_renewals:
            try:
                # Process renewal
                old_end_date = subscription.end_date
                subscription.start_date = old_end_date
                subscription.end_date = old_end_date + timedelta(days=30)
                subscription.next_billing_date = subscription.end_date
                subscription.save()
                
                # Create payment history record
                PaymentHistory.objects.create(
                    user=subscription.user,
                    payment_type=PaymentHistory.PaymentType.RENEWAL,
                    from_tier=subscription.tier,
                    to_tier=subscription.tier,
                    amount=subscription.amount_paid or 0,
                    description=f"자동 갱신: {subscription.get_tier_display()}"
                )
                
                # Send renewal notification email
                send_renewal_notification.delay(subscription.user.id, 'success')
                
                renewed_count += 1
                logger.info(f"Successfully renewed subscription for {subscription.user.email}")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to renew subscription for {subscription.user.email}: {str(e)}")
                # Send failure notification
                send_renewal_notification.delay(subscription.user.id, 'failed')
        
        # Check for expired subscriptions (past end_date with auto-renewal off)
        expired_subscriptions = Subscription.objects.filter(
            is_active=True,
            end_date__isnull=False,
            end_date__lte=now
        ).exclude(tier=SubscriptionTier.FREE)
        
        for subscription in expired_subscriptions:
            if not subscription.auto_renewal:
                # Downgrade to FREE tier
                old_tier = subscription.tier
                subscription.tier = SubscriptionTier.FREE
                subscription.is_active = True
                subscription.amount_paid = 0
                subscription.end_date = None
                subscription.next_billing_date = None
                subscription.save()
                
                # Create cancellation record
                PaymentHistory.objects.create(
                    user=subscription.user,
                    payment_type=PaymentHistory.PaymentType.CANCELLATION,
                    from_tier=old_tier,
                    to_tier=SubscriptionTier.FREE,
                    amount=0,
                    description=f"구독 만료: {old_tier} → FREE (자동갱신 비활성화)"
                )
                
                logger.info(f"Subscription expired for {subscription.user.email}, downgraded to FREE")
        
        logger.info(f"Subscription renewal check completed: {renewed_count} renewed, {failed_count} failed")
        return {'renewed': renewed_count, 'failed': failed_count}
        
    except Exception as e:
        logger.error(f"Error in subscription renewal check: {str(e)}")
        return {'error': str(e)}


@shared_task
def send_renewal_notification(user_id, status='success'):
    """Send subscription renewal notification email"""
    try:
        from .models import User
        user = User.objects.get(id=user_id)
        
        if status == 'success':
            subject = '[Resee] 구독이 자동으로 갱신되었습니다'
            template = 'accounts/renewal_success.html'
        else:
            subject = '[Resee] 구독 갱신에 실패했습니다'
            template = 'accounts/renewal_failed.html'
        
        context = {
            'user': user,
            'subscription': user.subscription,
            'profile_url': f"{settings.FRONTEND_URL}/profile",
        }
        
        html_message = render_to_string(template, context)
        plain_message = strip_tags(html_message)
        
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Renewal notification ({status}) sent to {user.email}")
        return True
        
    except User.DoesNotExist:
        logger.error(f"User with id {user_id} does not exist")
        return False
    except Exception as e:
        logger.error(f"Failed to send renewal notification: {str(e)}")
        return False