"""
Permission and subscription services for user accounts.
"""
from django.conf import settings


class PermissionService:
    """
    Service class to handle user permission checks and subscription logic.

    Centralizes permission-related business logic that was previously
    scattered across the User model methods.
    """

    def __init__(self, user):
        self.user = user

    def can_upgrade_subscription(self):
        """Check if user can upgrade subscription"""
        if getattr(settings, 'ENFORCE_EMAIL_VERIFICATION', True) and not self.user.is_email_verified:
            return False

        if hasattr(self.user, 'subscription') and self.user.subscription.tier == 'pro':
            return False

        return True


    def can_create_content(self):
        """Check if user can create more content based on subscription limit"""
        from content.models import Content
        current_count = Content.objects.filter(author=self.user).count()
        return current_count < self.get_content_limit()

    def can_create_category(self):
        """Check if user can create more categories based on subscription limit"""
        from content.models import Category
        current_count = Category.objects.filter(user=self.user).count()
        return current_count < self.get_category_limit()

    def get_content_limit(self):
        """Get content creation limit based on subscription tier"""
        tier = self._get_user_tier()

        tier_limits = {
            'free': 3,       # 3 contents for free users
            'basic': 10,     # 10 contents for basic users
            'pro': 50,       # 50 contents for pro users
        }

        return tier_limits.get(tier, 3)

    def get_category_limit(self):
        """Get category creation limit based on subscription tier"""
        tier = self._get_user_tier()

        tier_limits = {
            'free': 3,       # 3 categories for free users
            'basic': 15,     # 15 categories for basic users
            'pro': 50,       # 50 categories for pro users
        }

        return tier_limits.get(tier, 3)



    def get_content_usage(self):
        """Get content usage statistics for the user"""
        from content.models import Content
        current_count = Content.objects.filter(author=self.user).count()
        limit = self.get_content_limit()

        return {
            'current': current_count,
            'limit': limit,
            'remaining': max(0, limit - current_count),
            'percentage': (current_count / limit * 100) if limit > 0 else 0,
            'can_create': current_count < limit,
            'tier': self._get_user_tier()
        }

    def get_category_usage(self):
        """Get category usage statistics for the user"""
        from content.models import Category
        current_count = Category.objects.filter(user=self.user).count()
        limit = self.get_category_limit()

        return {
            'current': current_count,
            'limit': limit,
            'remaining': max(0, limit - current_count),
            'percentage': (current_count / limit * 100) if limit > 0 else 0,
            'can_create': current_count < limit,
            'tier': self._get_user_tier()
        }

    def _get_user_tier(self):
        """Get user's current subscription tier"""
        if not hasattr(self.user, 'subscription') or not self.user.subscription.is_active or self.user.subscription.is_expired():
            return 'free'
        return self.user.subscription.tier


class SubscriptionService:
    """
    Service class to handle subscription-related operations.
    """

    def __init__(self, user):
        self.user = user

    def has_active_subscription(self):
        """Check if user has an active subscription"""
        if not hasattr(self.user, 'subscription'):
            return False
        return self.user.subscription.is_active and not self.user.subscription.is_expired()

    def get_max_review_interval(self):
        """Get maximum review interval based on subscription"""
        if self.has_active_subscription():
            return self.user.subscription.max_interval_days
        return 3  # Default FREE tier