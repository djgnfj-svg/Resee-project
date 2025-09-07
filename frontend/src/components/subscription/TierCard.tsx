import React from 'react';
import { CheckIcon, XMarkIcon } from '@heroicons/react/24/outline';
import { SubscriptionTierInfo, SubscriptionTier } from '../../types';

interface TierCardProps {
  tier: SubscriptionTierInfo;
  currentTier?: string;
  billingCycle: 'monthly' | 'yearly';
  isPopular?: boolean;
  onUpgrade?: (tier: SubscriptionTier, billingCycle: 'monthly' | 'yearly') => void;
  upgrading?: boolean;
}

const TierCard: React.FC<TierCardProps> = ({
  tier,
  currentTier,
  billingCycle,
  isPopular = false,
  onUpgrade,
  upgrading = false,
}) => {
  const isCurrentTier = currentTier === tier.name;
  const canUpgrade = tier.name !== 'free' && !tier.coming_soon && !isCurrentTier;

  return (
    <div className={`relative bg-white dark:bg-gray-800 rounded-2xl shadow-lg dark:shadow-gray-900/25 border ${
      isPopular ? 'border-blue-500 dark:border-blue-400' : 'border-gray-200 dark:border-gray-700'
    } p-8 flex flex-col h-full`}>
      
      {isPopular && (
        <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
          <span className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-4 py-1 rounded-full text-sm font-medium">
            🔥 인기
          </span>
        </div>
      )}

      <div className="text-center mb-6">
        <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          {tier.display_name}
        </h3>
        
        <div className="mb-4">
          <span className="text-4xl font-bold text-gray-900 dark:text-gray-100">
            ₩{tier.price.toLocaleString()}
          </span>
          {tier.price > 0 && (
            <span className="text-gray-600 dark:text-gray-400 ml-2">
              / {billingCycle === 'monthly' ? '월' : '년'}
            </span>
          )}
        </div>

        {billingCycle === 'yearly' && tier.price > 0 && typeof tier.price === 'number' && (
          <div className="text-sm text-green-600 dark:text-green-400 mb-2">
            월 ₩{Math.floor(tier.price / 12).toLocaleString()} (연간 결제)
          </div>
        )}

        {tier.coming_soon && (
          <div className="inline-block bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 px-3 py-1 rounded-full text-sm font-medium mb-4">
            🚧 출시 예정
          </div>
        )}
      </div>

      <div className="flex-1 space-y-4 mb-8">
        {tier.features.map((feature, index) => (
          <div key={index} className="flex items-start">
            <CheckIcon className="h-5 w-5 text-green-500 mt-0.5 mr-3 flex-shrink-0" />
            <span className="text-gray-700 dark:text-gray-300 text-sm">{feature}</span>
          </div>
        ))}
      </div>

      <div className="mt-auto">
        {isCurrentTier ? (
          <div className="w-full bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 py-3 px-6 rounded-lg font-medium text-center">
            현재 플랜
          </div>
        ) : tier.coming_soon ? (
          <div className="w-full bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 py-3 px-6 rounded-lg font-medium text-center">
            출시 예정
          </div>
        ) : tier.name === 'free' ? (
          <div className="w-full bg-green-500 text-white py-3 px-6 rounded-lg font-medium text-center">
            무료 사용하기
          </div>
        ) : canUpgrade ? (
          <button
            onClick={() => onUpgrade?.(tier.name as SubscriptionTier, billingCycle)}
            disabled={upgrading}
            className={`w-full py-3 px-6 rounded-lg font-medium text-center transition-all duration-200 ${
              isPopular
                ? 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white'
                : 'bg-gray-900 dark:bg-white text-white dark:text-gray-900 hover:bg-gray-800 dark:hover:bg-gray-100'
            } disabled:opacity-50 disabled:cursor-not-allowed`}
          >
            {upgrading ? '처리 중...' : '업그레이드'}
          </button>
        ) : (
          <div className="w-full bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400 py-3 px-6 rounded-lg font-medium text-center">
            사용 불가
          </div>
        )}
      </div>
    </div>
  );
};

export default TierCard;