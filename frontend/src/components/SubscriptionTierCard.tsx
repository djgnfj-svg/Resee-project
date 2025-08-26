import React from 'react';
import { Check, Star, Crown, Zap, Shield } from 'lucide-react';
import { SubscriptionTierInfo, SubscriptionTier } from '../types';

const getTierIcon = (tier: SubscriptionTier) => {
  switch (tier) {
    case 'free':
      return <Shield className="w-6 h-6" />;
    case 'basic':
      return <Star className="w-6 h-6" />;
    case 'pro':
      return <Zap className="w-6 h-6" />;
    default:
      return <Shield className="w-6 h-6" />;
  }
};

const getTierColors = (tier: SubscriptionTier) => {
  switch (tier) {
    case 'free':
      return {
        border: 'border-gray-200',
        header: 'bg-gray-50',
        icon: 'text-gray-600',
        button: 'bg-gray-600 hover:bg-gray-700',
        accent: 'text-gray-600',
      };
    case 'basic':
      return {
        border: 'border-blue-200',
        header: 'bg-blue-50',
        icon: 'text-blue-600',
        button: 'bg-blue-600 hover:bg-blue-700',
        accent: 'text-blue-600',
      };
    case 'pro':
      return {
        border: 'border-yellow-300 shadow-lg',
        header: 'bg-gradient-to-r from-yellow-50 to-orange-50',
        icon: 'text-yellow-600',
        button: 'bg-gradient-to-r from-yellow-600 to-orange-600 hover:from-yellow-700 hover:to-orange-700',
        accent: 'text-yellow-600',
      };
    default:
      return {
        border: 'border-gray-200',
        header: 'bg-gray-50',
        icon: 'text-gray-600',
        button: 'bg-gray-600 hover:bg-gray-700',
        accent: 'text-gray-600',
      };
  }
};

interface SubscriptionTierCardProps {
  tier: SubscriptionTierInfo;
  currentTier?: SubscriptionTier;
  isLoading?: boolean;
  onSelect: (tier: SubscriptionTier) => void;
}

export const SubscriptionTierCard: React.FC<SubscriptionTierCardProps> = ({
  tier,
  currentTier,
  isLoading = false,
  onSelect,
}) => {
  const colors = getTierColors(tier.name);
  const isCurrentTier = currentTier === tier.name;
  const isDowngrade = currentTier === 'pro' && tier.name !== 'pro';
  const isUpgrade = currentTier && getTierPriority(tier.name) > getTierPriority(currentTier);
  
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('ko-KR', {
      style: 'currency',
      currency: 'KRW',
      minimumFractionDigits: 0,
    }).format(price);
  };

  function getTierPriority(tier: SubscriptionTier): number {
    const priorities = { free: 0, basic: 1, pro: 2 };
    return priorities[tier] ?? 0;
  }

  return (
    <div className={`relative bg-white rounded-xl border-2 ${colors.border} overflow-hidden transition-all hover:shadow-lg`}>
      {tier.name === 'pro' && (
        <div className="absolute top-0 right-0 bg-gradient-to-r from-yellow-400 to-orange-400 text-white text-xs font-bold px-3 py-1 rounded-bl-lg">
          인기
        </div>
      )}
      
      <div className={`${colors.header} px-6 py-4`}>
        <div className="flex items-center justify-center mb-2">
          <div className={`${colors.icon}`}>
            {getTierIcon(tier.name)}
          </div>
        </div>
        <h3 className="text-xl font-bold text-center text-gray-900">
          {tier.display_name}
        </h3>
      </div>
      
      <div className="px-6 py-4">
        <div className="text-center mb-4">
          <div className="text-3xl font-bold text-gray-900">
            {tier.price === 0 ? '무료' : formatPrice(Number(tier.price))}
          </div>
          {tier.price > 0 && (
            <div className="text-sm text-gray-500">월 구독</div>
          )}
        </div>
        
        <div className={`text-center mb-6 ${colors.accent} font-medium`}>
          최대 {tier.max_days}일까지 복습 지원
        </div>
        
        <ul className="space-y-3 mb-6">
          {tier.features.map((feature, index) => (
            <li key={index} className="flex items-start gap-3">
              <Check className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
              <span className="text-sm text-gray-700">{feature}</span>
            </li>
          ))}
        </ul>
        
        <button
          onClick={() => onSelect(tier.name)}
          disabled={isCurrentTier || isLoading}
          className={`
            w-full py-3 px-4 rounded-lg font-medium text-white transition-all
            ${isCurrentTier 
              ? 'bg-gray-300 cursor-not-allowed' 
              : `${colors.button} transform hover:scale-105`
            }
            ${isLoading ? 'opacity-50 cursor-not-allowed' : ''}
          `}
        >
          {isLoading ? '처리 중...' : 
           isCurrentTier ? '현재 플랜' :
           isDowngrade ? '다운그레이드' :
           isUpgrade ? '업그레이드' : 
           tier.name === 'free' ? '무료 시작' : '선택하기'}
        </button>
      </div>
    </div>
  );
};