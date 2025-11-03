import React from 'react';
import { CheckIcon } from '@heroicons/react/24/outline';
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

  return (
    <div className={`group relative bg-white dark:bg-gray-800 rounded-2xl shadow-lg dark:shadow-gray-900/25 border ${
      isPopular ? 'border-indigo-300 dark:border-indigo-700' : 'border-gray-200 dark:border-gray-700'
    } hover:shadow-xl transition-all duration-200 overflow-hidden flex flex-col h-full`}>

      {/* Top accent line */}
      <div className={`h-1 ${
        isPopular
          ? 'bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500'
          : 'bg-gradient-to-r from-gray-300 to-gray-400 dark:from-gray-600 dark:to-gray-700'
      }`}></div>

      <div className="p-8 flex flex-col flex-1">
        {isPopular && (
          <div className="absolute top-4 right-4">
            <span className="bg-gradient-to-r from-indigo-500 to-purple-500 text-white px-3 py-1 rounded-full text-xs font-semibold shadow-md">
              인기
            </span>
          </div>
        )}

        <div className="text-center mb-6">
          <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-4">
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
            <div className="inline-flex items-center gap-1 text-sm bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 px-3 py-1 rounded-full font-medium mb-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              월 ₩{Math.floor(tier.price / 12).toLocaleString()}
            </div>
          )}

          {tier.coming_soon && (
            <div className="inline-block bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300 px-3 py-1 rounded-full text-sm font-medium mb-4">
              출시 예정
            </div>
          )}
        </div>

        <div className="flex-1 space-y-3 mb-8">
          {tier.features.map((feature, index) => (
            <div key={index} className="flex items-start">
              <div className="flex-shrink-0 w-5 h-5 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mr-3 mt-0.5">
                <CheckIcon className="h-3 w-3 text-green-600 dark:text-green-400" />
              </div>
              <span className="text-gray-700 dark:text-gray-300 text-sm">{feature}</span>
            </div>
          ))}
        </div>

        <div className="mt-auto">
          {currentTier === tier.name ? (
            <div className="w-full bg-gradient-to-r from-green-500 to-green-600 text-white py-3 px-6 rounded-xl font-semibold text-center shadow-md">
              현재 {tier.display_name} 플랜
            </div>
          ) : tier.coming_soon ? (
            <div className="w-full bg-indigo-100 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 py-3 px-6 rounded-xl font-semibold text-center border-2 border-indigo-200 dark:border-indigo-700">
              사용자 20명 후 오픈
            </div>
          ) : (
            <button
              onClick={() => onUpgrade?.(tier.name as SubscriptionTier, billingCycle)}
              disabled={upgrading}
              className="w-full bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-500 text-white py-3 px-6 rounded-xl font-semibold transition-all duration-200 shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
            >
              {upgrading ? '처리 중...' : `${tier.display_name} 플랜 구독하기`}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default TierCard;