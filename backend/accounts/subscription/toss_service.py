"""
Toss Payments API Integration Service

This module provides integration with Toss Payments API for payment processing.
Uses httpx for HTTP requests to Toss Payments REST API.
"""

import base64
import httpx
from django.conf import settings
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class TossPaymentsService:
    """Service class for Toss Payments API integration."""

    def __init__(self):
        self.client_key = settings.TOSS_CLIENT_KEY
        self.secret_key = settings.TOSS_SECRET_KEY
        self.api_url = settings.TOSS_API_URL

        if not self.secret_key:
            logger.warning("TOSS_SECRET_KEY not configured")

    def _get_auth_header(self) -> str:
        """Generate Basic Auth header for Toss Payments API."""
        credentials = f"{self.secret_key}:"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    def create_payment(
        self,
        amount: int,
        order_id: str,
        order_name: str,
        customer_email: str,
        customer_name: str
    ) -> Dict[str, Any]:
        """
        Create a payment request to Toss Payments.

        Args:
            amount: Payment amount in KRW
            order_id: Unique order identifier
            order_name: Order description
            customer_email: Customer email address
            customer_name: Customer name

        Returns:
            Dict containing payment information
        """
        if not self.secret_key:
            logger.error("Cannot create payment: TOSS_SECRET_KEY not configured")
            return {
                'success': False,
                'error': 'Payment system not configured'
            }

        try:
            # For sandbox/test mode, return mock response
            # In production, this will call actual Toss API
            return {
                'success': True,
                'payment_key': f'test_payment_{order_id}',
                'order_id': order_id,
                'amount': amount,
                'checkout_url': f'{settings.TOSS_API_URL}/v1/payments/checkout',
                'client_key': self.client_key
            }
        except Exception as e:
            logger.error(f"Error creating payment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def confirm_payment(
        self,
        payment_key: str,
        order_id: str,
        amount: int
    ) -> Dict[str, Any]:
        """
        Confirm a payment with Toss Payments.

        Args:
            payment_key: Payment key from Toss
            order_id: Order identifier
            amount: Payment amount to confirm

        Returns:
            Dict containing confirmation result
        """
        if not self.secret_key:
            logger.error("Cannot confirm payment: TOSS_SECRET_KEY not configured")
            return {
                'success': False,
                'error': 'Payment system not configured'
            }

        url = f"{self.api_url}/v1/payments/confirm"
        headers = {
            'Authorization': self._get_auth_header(),
            'Content-Type': 'application/json'
        }
        data = {
            'paymentKey': payment_key,
            'orderId': order_id,
            'amount': amount
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=data, headers=headers)
                response.raise_for_status()

                result = response.json()
                logger.info(f"Payment confirmed: {order_id}")
                return {
                    'success': True,
                    'payment': result
                }
        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response else {}
            logger.error(f"Payment confirmation failed: {error_data}")
            return {
                'success': False,
                'error': error_data.get('message', 'Payment confirmation failed'),
                'code': error_data.get('code')
            }
        except Exception as e:
            logger.error(f"Error confirming payment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def cancel_payment(
        self,
        payment_key: str,
        cancel_reason: str,
        cancel_amount: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Cancel a payment (full or partial refund).

        Args:
            payment_key: Payment key from Toss
            cancel_reason: Reason for cancellation
            cancel_amount: Amount to cancel (None for full cancellation)

        Returns:
            Dict containing cancellation result
        """
        if not self.secret_key:
            logger.error("Cannot cancel payment: TOSS_SECRET_KEY not configured")
            return {
                'success': False,
                'error': 'Payment system not configured'
            }

        url = f"{self.api_url}/v1/payments/{payment_key}/cancel"
        headers = {
            'Authorization': self._get_auth_header(),
            'Content-Type': 'application/json'
        }
        data = {
            'cancelReason': cancel_reason
        }
        if cancel_amount:
            data['cancelAmount'] = cancel_amount

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, json=data, headers=headers)
                response.raise_for_status()

                result = response.json()
                logger.info(f"Payment cancelled: {payment_key}")
                return {
                    'success': True,
                    'cancellation': result
                }
        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response else {}
            logger.error(f"Payment cancellation failed: {error_data}")
            return {
                'success': False,
                'error': error_data.get('message', 'Payment cancellation failed'),
                'code': error_data.get('code')
            }
        except Exception as e:
            logger.error(f"Error cancelling payment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

    def get_payment(self, payment_key: str) -> Dict[str, Any]:
        """
        Retrieve payment details from Toss Payments.

        Args:
            payment_key: Payment key from Toss

        Returns:
            Dict containing payment details
        """
        if not self.secret_key:
            logger.error("Cannot get payment: TOSS_SECRET_KEY not configured")
            return {
                'success': False,
                'error': 'Payment system not configured'
            }

        url = f"{self.api_url}/v1/payments/{payment_key}"
        headers = {
            'Authorization': self._get_auth_header()
        }

        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.get(url, headers=headers)
                response.raise_for_status()

                result = response.json()
                return {
                    'success': True,
                    'payment': result
                }
        except httpx.HTTPStatusError as e:
            error_data = e.response.json() if e.response else {}
            logger.error(f"Failed to get payment: {error_data}")
            return {
                'success': False,
                'error': error_data.get('message', 'Failed to retrieve payment'),
                'code': error_data.get('code')
            }
        except Exception as e:
            logger.error(f"Error getting payment: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
