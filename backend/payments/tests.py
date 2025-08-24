"""
Test cases for payments application
"""
import json
from decimal import Decimal
from unittest.mock import patch, MagicMock

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import SubscriptionTier
from .models import PaymentPlan, Payment, Subscription as PaymentSubscription
from .services import (
    StripeService, WebhookHandler, PaymentError,
    PaymentValidationError, DuplicatePaymentError,
    InsufficientPermissionError
)
from .serializers import (
    PaymentPlanSerializer, CreatePaymentIntentSerializer,
    CreateSubscriptionSerializer, PaymentSerializer
)

User = get_user_model()


class PaymentPlanModelTest(TestCase):
    """Test PaymentPlan model"""
    
    def test_create_payment_plan(self):
        """Test creating a payment plan"""
        plan = PaymentPlan.objects.create(
            name='Basic Plan',
            tier=SubscriptionTier.BASIC,
            stripe_price_id_monthly='price_basic_monthly',
            stripe_price_id_yearly='price_basic_yearly',
            monthly_price=Decimal('9.99'),
            yearly_price=Decimal('99.99'),
            description='Basic plan features',
            features=['Feature 1', 'Feature 2'],
            is_active=True
        )
        
        self.assertEqual(plan.name, 'Basic Plan')
        self.assertEqual(plan.tier, SubscriptionTier.BASIC)
        self.assertEqual(plan.monthly_price, Decimal('9.99'))
        self.assertEqual(plan.yearly_price, Decimal('99.99'))
        self.assertTrue(plan.is_active)
        self.assertEqual(len(plan.features), 2)
    
    def test_yearly_discount_percentage(self):
        """Test yearly discount percentage calculation"""
        plan = PaymentPlan.objects.create(
            name='Pro Plan',
            tier=SubscriptionTier.PRO,
            monthly_price=Decimal('19.99'),
            yearly_price=Decimal('199.99'),  # 2 months free
        )
        
        # 12 * 19.99 = 239.88, discount = (239.88 - 199.99) / 239.88 * 100 = 16.6%
        discount = plan.yearly_discount_percentage
        self.assertAlmostEqual(discount, 16.6, places=1)
    
    def test_plan_str_representation(self):
        """Test plan string representation"""
        plan = PaymentPlan.objects.create(
            name='Test Plan',
            tier=SubscriptionTier.BASIC,
            monthly_price=Decimal('10.00'),
            yearly_price=Decimal('100.00')
        )
        
        self.assertEqual(str(plan), 'Test Plan (Basic (90일))')


class PaymentModelTest(TestCase):
    """Test Payment model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.plan = PaymentPlan.objects.create(
            name='Test Plan',
            tier=SubscriptionTier.BASIC,
            monthly_price=Decimal('9.99'),
            yearly_price=Decimal('99.99')
        )
    
    def test_create_payment(self):
        """Test creating a payment record"""
        payment = Payment.objects.create(
            user=self.user,
            plan=self.plan,
            amount=Decimal('9.99'),
            currency='USD',
            billing_cycle=Payment.BillingCycle.MONTHLY,
            status=Payment.Status.PENDING,
            stripe_payment_intent_id='pi_test_123'
        )
        
        self.assertEqual(payment.user, self.user)
        self.assertEqual(payment.plan, self.plan)
        self.assertEqual(payment.amount, Decimal('9.99'))
        self.assertEqual(payment.currency, 'USD')
        self.assertEqual(payment.billing_cycle, Payment.BillingCycle.MONTHLY)
        self.assertEqual(payment.status, Payment.Status.PENDING)
    
    def test_payment_success_updates(self):
        """Test payment success updates"""
        payment = Payment.objects.create(
            user=self.user,
            plan=self.plan,
            amount=Decimal('9.99'),
            currency='USD',
            billing_cycle=Payment.BillingCycle.MONTHLY,
            status=Payment.Status.PENDING,
            stripe_payment_intent_id='pi_test_123'
        )
        
        # Simulate successful payment
        payment.status = Payment.Status.SUCCEEDED
        payment.stripe_payment_id = 'py_test_123'
        payment.paid_at = timezone.now()
        payment.save()
        
        self.assertEqual(payment.status, Payment.Status.SUCCEEDED)
        self.assertIsNotNone(payment.paid_at)
        self.assertEqual(payment.stripe_payment_id, 'py_test_123')
    
    def test_payment_str_representation(self):
        """Test payment string representation"""
        payment = Payment.objects.create(
            user=self.user,
            plan=self.plan,
            amount=Decimal('9.99'),
            currency='USD',
            billing_cycle=Payment.BillingCycle.MONTHLY,
            status=Payment.Status.SUCCEEDED
        )
        
        expected_str = f"{self.user.email} - Test Plan (9.99 USD) - 성공"
        self.assertEqual(str(payment), expected_str)


class PaymentSubscriptionModelTest(TestCase):
    """Test PaymentSubscription model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.plan = PaymentPlan.objects.create(
            name='Test Plan',
            tier=SubscriptionTier.BASIC,
            monthly_price=Decimal('9.99'),
            yearly_price=Decimal('99.99')
        )
    
    def test_create_subscription(self):
        """Test creating a subscription"""
        subscription = PaymentSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_subscription_id='sub_test_123',
            status=PaymentSubscription.Status.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30)
        )
        
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.plan, self.plan)
        self.assertEqual(subscription.status, PaymentSubscription.Status.ACTIVE)
        self.assertIsNotNone(subscription.current_period_start)
        self.assertIsNotNone(subscription.current_period_end)


class StripeServiceTest(TestCase):
    """Test StripeService"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_email_verified = True
        self.user.save()
        
        self.plan = PaymentPlan.objects.create(
            name='Test Plan',
            tier=SubscriptionTier.BASIC,
            stripe_price_id_monthly='price_test_monthly',
            monthly_price=Decimal('9.99'),
            yearly_price=Decimal('99.99')
        )
    
    @patch('stripe.PaymentIntent.create')
    @patch('stripe.Customer.create')
    def test_create_payment_intent_success(self, mock_customer_create, mock_payment_intent_create):
        """Test successful payment intent creation"""
        mock_customer = MagicMock()
        mock_customer.id = 'cus_test_123'
        mock_customer_create.return_value = mock_customer
        
        mock_intent = MagicMock()
        mock_intent.id = 'pi_test_123'
        mock_intent.client_secret = 'pi_test_123_secret_xyz'
        mock_intent.amount = 999  # $9.99 in cents
        mock_payment_intent_create.return_value = mock_intent
        
        intent, payment = StripeService.create_payment_intent(
            user=self.user,
            plan=self.plan,
            billing_cycle='monthly'
        )
        
        self.assertEqual(intent.id, 'pi_test_123')
        self.assertEqual(payment.amount, Decimal('9.99'))
        self.assertEqual(payment.status, Payment.Status.PENDING)
        self.assertEqual(payment.stripe_payment_intent_id, 'pi_test_123')
    
    @patch('stripe.Customer.create')
    def test_create_payment_intent_stripe_error(self, mock_customer_create):
        """Test payment intent creation with Stripe error"""
        mock_customer_create.side_effect = Exception("Stripe API Error")
        
        with self.assertRaises(PaymentError):
            StripeService.create_payment_intent(
                user=self.user,
                plan=self.plan,
                billing_cycle='monthly'
            )
    
    def test_create_payment_intent_duplicate_pending(self):
        """Test duplicate payment intent prevention"""
        # Create existing pending payment
        Payment.objects.create(
            user=self.user,
            plan=self.plan,
            amount=Decimal('9.99'),
            currency='USD',
            billing_cycle=Payment.BillingCycle.MONTHLY,
            status=Payment.Status.PENDING,
            stripe_payment_intent_id='pi_existing_123'
        )
        
        with self.assertRaises(DuplicatePaymentError):
            StripeService.create_payment_intent(
                user=self.user,
                plan=self.plan,
                billing_cycle='monthly'
            )
    
    def test_create_payment_intent_unverified_email(self):
        """Test payment intent creation with unverified email"""
        self.user.is_email_verified = False
        self.user.save()
        
        with self.assertRaises(InsufficientPermissionError):
            StripeService.create_payment_intent(
                user=self.user,
                plan=self.plan,
                billing_cycle='monthly'
            )
    
    @patch('stripe.Subscription.create')
    @patch('stripe.Customer.create')
    def test_create_subscription_success(self, mock_customer_create, mock_subscription_create):
        """Test successful subscription creation"""
        mock_customer = MagicMock()
        mock_customer.id = 'cus_test_123'
        mock_customer_create.return_value = mock_customer
        
        mock_subscription = MagicMock()
        mock_subscription.id = 'sub_test_123'
        mock_subscription.status = 'active'
        mock_subscription.current_period_start = 1234567890
        mock_subscription.current_period_end = 1234567890 + 2592000  # +30 days
        mock_subscription_create.return_value = mock_subscription
        
        subscription = StripeService.create_subscription(
            user=self.user,
            plan=self.plan,
            payment_method_id='pm_test_123'
        )
        
        self.assertEqual(subscription.stripe_subscription_id, 'sub_test_123')
        self.assertEqual(subscription.status, PaymentSubscription.Status.ACTIVE)
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.plan, self.plan)
    
    @patch('stripe.Subscription.modify')
    def test_cancel_subscription_success(self, mock_subscription_modify):
        """Test successful subscription cancellation"""
        subscription = PaymentSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_subscription_id='sub_test_123',
            status=PaymentSubscription.Status.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30)
        )
        
        mock_subscription = MagicMock()
        mock_subscription.status = 'canceled'
        mock_subscription_modify.return_value = mock_subscription
        
        cancelled_subscription = StripeService.cancel_subscription(subscription)
        
        self.assertEqual(cancelled_subscription.status, PaymentSubscription.Status.CANCELED)


class WebhookHandlerTest(TestCase):
    """Test WebhookHandler"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.plan = PaymentPlan.objects.create(
            name='Test Plan',
            tier=SubscriptionTier.BASIC,
            monthly_price=Decimal('9.99'),
            yearly_price=Decimal('99.99')
        )
    
    def test_handle_payment_succeeded(self):
        """Test handling successful payment webhook"""
        # Create pending payment
        payment = Payment.objects.create(
            user=self.user,
            plan=self.plan,
            amount=Decimal('9.99'),
            currency='USD',
            billing_cycle=Payment.BillingCycle.MONTHLY,
            status=Payment.Status.PENDING,
            stripe_payment_intent_id='pi_test_123'
        )
        
        webhook_data = {
            'id': 'pi_test_123',
            'status': 'succeeded',
            'charges': {
                'data': [{'id': 'ch_test_123'}]
            }
        }
        
        WebhookHandler.handle_payment_intent_succeeded(webhook_data)
        
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.SUCCEEDED)
        self.assertIsNotNone(payment.paid_at)
    
    def test_handle_payment_failed(self):
        """Test handling failed payment webhook"""
        payment = Payment.objects.create(
            user=self.user,
            plan=self.plan,
            amount=Decimal('9.99'),
            currency='USD',
            billing_cycle=Payment.BillingCycle.MONTHLY,
            status=Payment.Status.PENDING,
            stripe_payment_intent_id='pi_test_123'
        )
        
        webhook_data = {
            'id': 'pi_test_123',
            'status': 'payment_failed',
            'last_payment_error': {
                'message': 'Your card was declined.'
            }
        }
        
        WebhookHandler.handle_payment_intent_failed(webhook_data)
        
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.FAILED)
        self.assertIsNotNone(payment.failure_reason)
    
    def test_handle_subscription_created(self):
        """Test handling subscription created webhook"""
        webhook_data = {
            'id': 'sub_test_123',
            'customer': 'cus_test_123',
            'status': 'active',
            'current_period_start': 1234567890,
            'current_period_end': 1234567890 + 2592000,
            'items': {
                'data': [
                    {
                        'price': {
                            'id': self.plan.stripe_price_id_monthly
                        }
                    }
                ]
            }
        }
        
        with patch('payments.services.User.objects.get') as mock_get_user:
            mock_get_user.return_value = self.user
            
            WebhookHandler.handle_subscription_created(webhook_data)
        
        # Check if subscription was created
        subscription = PaymentSubscription.objects.filter(
            stripe_subscription_id='sub_test_123'
        ).first()
        
        self.assertIsNotNone(subscription)
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.status, PaymentSubscription.Status.ACTIVE)


class PaymentAPITest(APITestCase):
    """Test Payment API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.user.is_email_verified = True
        self.user.save()
        
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        self.plan = PaymentPlan.objects.create(
            name='Test Plan',
            tier=SubscriptionTier.BASIC,
            stripe_price_id_monthly='price_test_monthly',
            stripe_price_id_yearly='price_test_yearly',
            monthly_price=Decimal('9.99'),
            yearly_price=Decimal('99.99'),
            description='Test plan',
            features=['Feature 1', 'Feature 2'],
            is_active=True
        )
    
    def test_payment_plans_list(self):
        """Test listing payment plans"""
        url = reverse('payments:payment-plans')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Test Plan')
        self.assertEqual(response.data[0]['monthly_price'], '9.99')
        self.assertIn('yearly_discount_percentage', response.data[0])
    
    @patch('payments.services.StripeService.create_payment_intent')
    def test_create_payment_intent_success(self, mock_create_intent):
        """Test successful payment intent creation"""
        mock_intent = MagicMock()
        mock_intent.client_secret = 'pi_test_123_secret'
        
        mock_payment = MagicMock()
        mock_payment.id = 1
        mock_payment.amount = Decimal('9.99')
        
        mock_create_intent.return_value = (mock_intent, mock_payment)
        
        url = reverse('payments:create-payment-intent')
        data = {
            'plan_id': self.plan.id,
            'billing_cycle': 'monthly'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('client_secret', response.data)
        self.assertIn('payment_id', response.data)
        self.assertEqual(response.data['amount'], '9.99')
    
    def test_create_payment_intent_invalid_plan(self):
        """Test payment intent creation with invalid plan"""
        url = reverse('payments:create-payment-intent')
        data = {
            'plan_id': 99999,
            'billing_cycle': 'monthly'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_create_payment_intent_unverified_email(self):
        """Test payment intent creation with unverified email"""
        self.user.is_email_verified = False
        self.user.save()
        
        url = reverse('payments:create-payment-intent')
        data = {
            'plan_id': self.plan.id,
            'billing_cycle': 'monthly'
        }
        
        with patch('payments.services.StripeService.create_payment_intent') as mock_create:
            mock_create.side_effect = InsufficientPermissionError("Email not verified")
            
            response = self.client.post(url, data, format='json')
            
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    @patch('payments.services.StripeService.create_subscription')
    def test_create_subscription_success(self, mock_create_subscription):
        """Test successful subscription creation"""
        mock_subscription = MagicMock()
        mock_subscription.id = 1
        mock_subscription.stripe_subscription_id = 'sub_test_123'
        mock_subscription.status = PaymentSubscription.Status.ACTIVE
        
        mock_create_subscription.return_value = mock_subscription
        
        url = reverse('payments:create-subscription')
        data = {
            'plan_id': self.plan.id,
            'payment_method_id': 'pm_test_123'
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['stripe_subscription_id'], 'sub_test_123')
    
    def test_payment_history(self):
        """Test payment history listing"""
        # Create some payment history
        Payment.objects.create(
            user=self.user,
            plan=self.plan,
            amount=Decimal('9.99'),
            currency='USD',
            billing_cycle=Payment.BillingCycle.MONTHLY,
            status=Payment.Status.SUCCEEDED,
            stripe_payment_intent_id='pi_test_123',
            paid_at=timezone.now()
        )
        
        url = reverse('payments:payment-history')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['status'], '성공')
        self.assertEqual(response.data['results'][0]['amount'], '9.99')
    
    def test_subscription_status(self):
        """Test subscription status endpoint"""
        # Create active subscription
        PaymentSubscription.objects.create(
            user=self.user,
            plan=self.plan,
            stripe_subscription_id='sub_test_123',
            status=PaymentSubscription.Status.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timezone.timedelta(days=30)
        )
        
        url = reverse('payments:subscription-status')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], PaymentSubscription.Status.ACTIVE)
        self.assertIn('current_period_end', response.data)
        self.assertIn('plan', response.data)
    
    @patch('stripe.Webhook.construct_event')
    def test_stripe_webhook_valid(self, mock_construct_event):
        """Test valid Stripe webhook processing"""
        webhook_data = {
            'type': 'payment_intent.succeeded',
            'data': {
                'object': {
                    'id': 'pi_test_123',
                    'status': 'succeeded'
                }
            }
        }
        
        mock_construct_event.return_value = webhook_data
        
        url = reverse('payments:stripe-webhook')
        
        with patch('payments.services.WebhookHandler.handle_payment_intent_succeeded') as mock_handle:
            response = self.client.post(
                url,
                json.dumps(webhook_data),
                content_type='application/json',
                HTTP_STRIPE_SIGNATURE='test_signature'
            )
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            mock_handle.assert_called_once()
    
    @patch('stripe.Webhook.construct_event')
    def test_stripe_webhook_invalid_signature(self, mock_construct_event):
        """Test Stripe webhook with invalid signature"""
        mock_construct_event.side_effect = Exception("Invalid signature")
        
        url = reverse('payments:stripe-webhook')
        
        response = self.client.post(
            url,
            '{"type": "test"}',
            content_type='application/json',
            HTTP_STRIPE_SIGNATURE='invalid_signature'
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SerializerTest(TestCase):
    """Test payment serializers"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.plan = PaymentPlan.objects.create(
            name='Test Plan',
            tier=SubscriptionTier.BASIC,
            monthly_price=Decimal('9.99'),
            yearly_price=Decimal('99.99')
        )
    
    def test_payment_plan_serializer(self):
        """Test PaymentPlanSerializer"""
        serializer = PaymentPlanSerializer(self.plan)
        
        data = serializer.data
        self.assertEqual(data['name'], 'Test Plan')
        self.assertEqual(data['monthly_price'], '9.99')
        self.assertEqual(data['yearly_price'], '99.99')
        self.assertIn('yearly_discount_percentage', data)
    
    def test_create_payment_intent_serializer_valid(self):
        """Test CreatePaymentIntentSerializer with valid data"""
        data = {
            'plan_id': self.plan.id,
            'billing_cycle': 'monthly'
        }
        
        serializer = CreatePaymentIntentSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data['plan_id'], self.plan.id)
        self.assertEqual(serializer.validated_data['billing_cycle'], 'monthly')
    
    def test_create_payment_intent_serializer_invalid(self):
        """Test CreatePaymentIntentSerializer with invalid data"""
        data = {
            'plan_id': self.plan.id,
            'billing_cycle': 'invalid_cycle'
        }
        
        serializer = CreatePaymentIntentSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('billing_cycle', serializer.errors)
    
    def test_create_subscription_serializer_valid(self):
        """Test CreateSubscriptionSerializer with valid data"""
        data = {
            'plan_id': self.plan.id,
            'payment_method_id': 'pm_test_123'
        }
        
        serializer = CreateSubscriptionSerializer(data=data)
        self.assertTrue(serializer.is_valid())
    
    def test_payment_serializer(self):
        """Test PaymentSerializer"""
        payment = Payment.objects.create(
            user=self.user,
            plan=self.plan,
            amount=Decimal('9.99'),
            currency='USD',
            billing_cycle=Payment.BillingCycle.MONTHLY,
            status=Payment.Status.SUCCEEDED
        )
        
        serializer = PaymentSerializer(payment)
        
        data = serializer.data
        self.assertEqual(data['amount'], '9.99')
        self.assertEqual(data['currency'], 'USD')
        self.assertEqual(data['status'], '성공')
        self.assertIn('plan', data)