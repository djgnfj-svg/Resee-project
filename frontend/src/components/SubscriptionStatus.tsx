import React from 'react';
import { Shield, Star, Zap } from 'lucide-react';
import { useSubscription } from '../hooks/useSubscription';
import type { SubscriptionTier } from '../types';

const getTierIcon = (tier: SubscriptionTier) => {
  switch (tier) {
    case 'free':
      return <Shield className="w-4 h-4" />;
    case 'basic':
      return <Star className="w-4 h-4" />;
    case 'pro':
      return <Zap className="w-4 h-4" />;
    default:
      return <Shield className="w-4 h-4" />;
  }
};

const getTierColor = (tier: SubscriptionTier) => {
  switch (tier) {
    case 'free':
      return 'bg-gray-100 text-gray-800 border-gray-200';
    case 'basic':
      return 'bg-indigo-100 text-indigo-800 border-indigo-200';
    case 'pro':
      return 'bg-yellow-100 text-yellow-800 border-yellow-200';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-200';
  }
};

interface SubscriptionStatusProps {
  showUpgradeButton?: boolean;
  onUpgradeClick?: () => void;
  className?: string;
}

export const SubscriptionStatus: React.FC<SubscriptionStatusProps> = ({
  showUpgradeButton = false,
  onUpgradeClick,
  className = '',
}) => {
  const { subscription, isLoadingSubscription } = useSubscription();

  if (isLoadingSubscription) {
    return (
      <div className={`animate-pulse bg-gray-200 h-8 rounded-lg ${className}`} />
    );
  }

  if (!subscription) {
    return null;
  }

  const isExpired = subscription.is_expired;
  const daysRemaining = subscription.days_remaining;

  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <div className={`flex items-center gap-2 px-3 py-1 rounded-full border ${getTierColor(subscription.tier)}`}>
        {getTierIcon(subscription.tier)}
        <span className="text-sm font-medium">
          {subscription.tier_display}
        </span>
      </div>
      
      <div className="text-sm text-gray-600">
        <span>최대 {subscription.max_interval_days}일 복습</span>
        {daysRemaining !== null && (
          <span className="ml-2">
            ({daysRemaining}일 남음)
          </span>
        )}
        {isExpired && (
          <span className="ml-2 text-red-600 font-medium">
            (만료됨)
          </span>
        )}
      </div>
      
      {showUpgradeButton && subscription.tier !== 'pro' && (
        <button
          onClick={onUpgradeClick}
          className="text-sm bg-indigo-600 text-white px-3 py-1 rounded-lg hover:bg-indigo-700 transition-colors"
        >
          업그레이드
        </button>
      )}
    </div>
  );
};