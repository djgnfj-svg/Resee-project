import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { authAPI } from '../utils/api';
import { User } from '../types';
import NotificationTab from '../components/settings/NotificationTab';
import SecurityTab from '../components/settings/SecurityTab';


const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'notifications' | 'security'>('notifications');

  // Fetch user profile
  const { isLoading } = useQuery<User>({
    queryKey: ['profile'],
    queryFn: authAPI.getProfile,
  });


  const tabs = [
    { id: 'notifications', name: '알림 설정', icon: '' },
    { id: 'security', name: '보안', icon: '' },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">설정</h1>
        <p className="mt-2 text-gray-600 dark:text-gray-400">
          계정 설정과 환경을 관리할 수 있습니다.
        </p>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
        {/* Tabs - Mobile Responsive */}
        <div className="border-b border-gray-200 dark:border-gray-700">
          {/* Mobile Tab Selector */}
          <div className="block sm:hidden p-4">
            <select
              value={activeTab}
              onChange={(e) => setActiveTab(e.target.value as any)}
              className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            >
              {tabs.map((tab) => (
                <option key={tab.id} value={tab.id}>
                  {tab.icon} {tab.name}
                </option>
              ))}
            </select>
          </div>

          {/* Desktop Tabs */}
          <nav className="hidden sm:flex space-x-8 px-6" aria-label="Tabs">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                className={`py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300 hover:border-gray-300 dark:hover:border-gray-600'
                }`}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.name}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="p-4 sm:p-6">
          {/* Notifications Tab */}
          {activeTab === 'notifications' && <NotificationTab />}

          {/* Security Tab */}
          {activeTab === 'security' && <SecurityTab />}
        </div>
      </div>
    </div>
  );
};

export default SettingsPage;