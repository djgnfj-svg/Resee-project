import React from 'react';
import { Link } from 'react-router-dom';
import { CreditCardIcon } from '@heroicons/react/24/outline';
import { User } from '../../types';

interface SubscriptionManagementProps {
  user: User;
}

const SubscriptionManagement: React.FC<SubscriptionManagementProps> = ({ user }) => {
  const handleComingSoon = () => {
    alert('결제 시스템은 12월에 오픈 예정입니다.\n\n현재는 모든 기능을 무료로 이용하실 수 있습니다.');
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">구독 정보</h3>
      {user.subscription ? (
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">현재 플랜</span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {user.subscription.tier_display}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">상태</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${
              user.subscription.is_active
                ? 'bg-green-100 text-green-800'
                : 'bg-gray-100 text-gray-800'
            }`}>
              {user.subscription.is_active ? '활성' : '비활성'}
            </span>
          </div>
          <div className="flex justify-between items-center">
            <span className="text-sm text-gray-600 dark:text-gray-400">최대 복습 간격</span>
            <span className="font-medium text-gray-900 dark:text-gray-100">
              {user.subscription.max_interval_days}일
            </span>
          </div>
          {user.subscription.days_remaining && (
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600 dark:text-gray-400">남은 기간</span>
              <span className="font-medium text-gray-900 dark:text-gray-100">
                {user.subscription.days_remaining}일
              </span>
            </div>
          )}
          <div className="pt-3 border-t space-y-2">
            <Link
              to="/subscription"
              className="w-full flex items-center justify-center px-4 py-2 text-sm font-medium text-indigo-600 hover:text-indigo-700 border border-indigo-600 hover:border-indigo-700 rounded-lg transition-colors"
            >
              <CreditCardIcon className="w-4 h-4 mr-2" />
              구독 관리
            </Link>
            {user.subscription.tier !== 'free' && (
              <button
                onClick={handleComingSoon}
                className="w-full flex items-center justify-center px-4 py-2 text-sm font-medium text-gray-600 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 border border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500 rounded-lg transition-colors"
              >
                <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                구독 취소 (12월 오픈)
              </button>
            )}
          </div>
        </div>
      ) : (
        <div className="text-center py-4">
          <p className="text-gray-500 dark:text-gray-400 mb-4">구독 정보가 없습니다</p>
          <Link
            to="/subscription"
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors"
          >
            <CreditCardIcon className="w-4 h-4 mr-2" />
            구독하기
          </Link>
        </div>
      )}
    </div>
  );
};

export default SubscriptionManagement;