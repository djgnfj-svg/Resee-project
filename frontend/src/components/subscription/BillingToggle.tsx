import React from 'react';

interface BillingToggleProps {
  billingCycle: 'monthly' | 'yearly';
  setBillingCycle: (cycle: 'monthly' | 'yearly') => void;
}

const BillingToggle: React.FC<BillingToggleProps> = ({
  billingCycle,
  setBillingCycle,
}) => {
  return (
    <div className="flex justify-center mb-12">
      <div className="bg-gray-100 dark:bg-gray-800 p-1 rounded-lg">
        <div className="flex">
          <button
            onClick={() => setBillingCycle('monthly')}
            className={`px-6 py-2 text-sm font-medium rounded-md transition-all duration-200 ${
              billingCycle === 'monthly'
                ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
            }`}
          >
            월간 결제
          </button>
          <button
            onClick={() => setBillingCycle('yearly')}
            className={`px-6 py-2 text-sm font-medium rounded-md transition-all duration-200 relative ${
              billingCycle === 'yearly'
                ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm'
                : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-100'
            }`}
          >
            연간 결제
            <span className="absolute -top-2 -right-2 bg-green-500 text-white text-xs px-2 py-0.5 rounded-full">
              20% 할인
            </span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default BillingToggle;