import React, { useState, useEffect } from 'react';
import { 
  ChartBarIcon, 
  ExclamationTriangleIcon, 
  CpuChipIcon, 
  ClockIcon,
  UserGroupIcon,
  ServerIcon,
  BellIcon,
  Cog6ToothIcon
} from '@heroicons/react/24/outline';
import { Layout } from '../components/Layout';
import { SystemStatusCard } from '../components/monitoring/SystemStatusCard';
import { PerformanceChart } from '../components/monitoring/PerformanceChart';
import { ErrorLogTable } from '../components/monitoring/ErrorLogTable';
import { AlertPanel } from '../components/monitoring/AlertPanel';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { useDashboardOverview, useAlertHistory, useAlertStatistics } from '../hooks/monitoring/useMonitoring';
import type { MonitoringFilters } from '../types/monitoring';

const MonitoringDashboard: React.FC = () => {
  const [filters, setFilters] = useState<MonitoringFilters>({
    timeRange: '24h',
  });
  const [activeTab, setActiveTab] = useState<'overview' | 'alerts' | 'system' | 'logs'>('overview');

  const { 
    data: dashboardData, 
    isLoading: isDashboardLoading, 
    error: dashboardError 
  } = useDashboardOverview();

  const { 
    data: alertHistoryData, 
    isLoading: isAlertsLoading 
  } = useAlertHistory({ hours: 24 });

  const { 
    data: alertStats, 
    isLoading: isStatsLoading 
  } = useAlertStatistics();

  // Auto-refresh every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      // React Query will handle the refetching automatically
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  if (isDashboardLoading && !dashboardData) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <LoadingSpinner size="large" />
        </div>
      </Layout>
    );
  }

  if (dashboardError) {
    return (
      <Layout>
        <div className="flex items-center justify-center min-h-screen">
          <div className="text-center">
            <ExclamationTriangleIcon className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
              모니터링 데이터를 불러올 수 없습니다
            </h2>
            <p className="text-gray-600 dark:text-gray-400">
              잠시 후 다시 시도해주세요.
            </p>
          </div>
        </div>
      </Layout>
    );
  }

  const getSystemStatus = () => {
    if (!dashboardData?.system_health) return 'warning';
    
    const { cpu_usage_percent, memory_usage_percent, api_error_rate_percent } = dashboardData.system_health;
    
    if (cpu_usage_percent > 80 || memory_usage_percent > 80 || api_error_rate_percent > 5) {
      return 'critical';
    }
    if (cpu_usage_percent > 60 || memory_usage_percent > 60 || api_error_rate_percent > 2) {
      return 'warning';
    }
    return 'healthy';
  };

  const tabs = [
    { id: 'overview', name: '개요', icon: ChartBarIcon },
    { id: 'alerts', name: '알림', icon: BellIcon },
    { id: 'system', name: '시스템', icon: ServerIcon },
    { id: 'logs', name: '로그', icon: ExclamationTriangleIcon },
  ];

  return (
    <Layout>
      <div className="space-y-6">
        {/* Header */}
        <div className="md:flex md:items-center md:justify-between">
          <div className="min-w-0 flex-1">
            <h1 className="text-2xl font-bold leading-7 text-gray-900 dark:text-gray-100 sm:truncate sm:text-3xl sm:tracking-tight">
              시스템 모니터링
            </h1>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              실시간 시스템 상태 및 알림 관리
            </p>
          </div>
          <div className="mt-4 flex md:ml-4 md:mt-0">
            <button
              type="button"
              className="inline-flex items-center rounded-md bg-white dark:bg-gray-800 px-3 py-2 text-sm font-semibold text-gray-900 dark:text-gray-100 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700"
            >
              <Cog6ToothIcon className="-ml-0.5 mr-1.5 h-5 w-5" />
              설정
            </button>
          </div>
        </div>

        {/* Status Cards */}
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <SystemStatusCard
            title="시스템 상태"
            value={getSystemStatus() === 'healthy' ? '정상' : getSystemStatus() === 'warning' ? '주의' : '위험'}
            status={getSystemStatus()}
            icon={<ServerIcon className="h-6 w-6" />}
            loading={isDashboardLoading}
          />
          
          <SystemStatusCard
            title="API 응답시간"
            value={dashboardData?.api_metrics.avg_response_time_ms || 0}
            unit="ms"
            status={
              (dashboardData?.api_metrics.avg_response_time_ms || 0) > 500 ? 'critical' :
              (dashboardData?.api_metrics.avg_response_time_ms || 0) > 200 ? 'warning' : 'healthy'
            }
            icon={<ClockIcon className="h-6 w-6" />}
            loading={isDashboardLoading}
          />
          
          <SystemStatusCard
            title="활성 사용자"
            value={dashboardData?.user_activity.active_users_today || 0}
            status="healthy"
            icon={<UserGroupIcon className="h-6 w-6" />}
            loading={isDashboardLoading}
          />
          
          <SystemStatusCard
            title="미해결 알림"
            value={alertStats?.unresolved_alerts || 0}
            status={
              (alertStats?.unresolved_alerts || 0) > 10 ? 'critical' :
              (alertStats?.unresolved_alerts || 0) > 5 ? 'warning' : 'healthy'
            }
            icon={<BellIcon className="h-6 w-6" />}
            loading={isStatsLoading}
          />
        </div>

        {/* Time Range Filter */}
        <div className="flex space-x-1 rounded-lg bg-gray-100 dark:bg-gray-800 p-1">
          {[
            { key: '1h', label: '1시간' },
            { key: '24h', label: '24시간' },
            { key: '7d', label: '7일' },
            { key: '30d', label: '30일' }
          ].map(({ key, label }) => (
            <button
              key={key}
              onClick={() => setFilters({ ...filters, timeRange: key as any })}
              className={`${
                filters.timeRange === key
                  ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 shadow'
                  : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200'
              } rounded-md px-3 py-1.5 text-sm font-medium transition-all duration-200`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 dark:border-gray-700">
          <nav className="-mb-px flex space-x-8">
            {tabs.map(({ id, name, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id as any)}
                className={`${
                  activeTab === id
                    ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                    : 'border-transparent text-gray-500 dark:text-gray-400 hover:border-gray-300 hover:text-gray-700 dark:hover:text-gray-300'
                } flex items-center whitespace-nowrap border-b-2 py-4 px-1 text-sm font-medium`}
              >
                <Icon className="mr-2 h-5 w-5" />
                {name}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        <div className="space-y-6">
          {activeTab === 'overview' && (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              {/* API Performance Chart */}
              <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
                    API 성능
                  </h3>
                  <PerformanceChart
                    data={[
                      { timestamp: '09:00', value: dashboardData?.api_metrics.avg_response_time_ms || 0 },
                      // This would be populated with real time-series data
                    ]}
                    timeRange={filters.timeRange}
                    title="평균 응답시간"
                    height={300}
                    loading={isDashboardLoading}
                  />
                </div>
              </div>

              {/* User Activity Chart */}
              <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                  <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">
                    사용자 활동
                  </h3>
                  <div className="space-y-4">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-400">오늘 활성 사용자</span>
                      <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {dashboardData?.user_activity.active_users_today || 0}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-400">API 요청</span>
                      <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {dashboardData?.user_activity.total_api_requests || 0}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-400">생성된 콘텐츠</span>
                      <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {dashboardData?.user_activity.total_content_created || 0}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600 dark:text-gray-400">완료된 복습</span>
                      <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
                        {dashboardData?.user_activity.total_reviews_completed || 0}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'alerts' && (
            <AlertPanel 
              alerts={alertHistoryData?.results || []}
              statistics={alertStats}
              loading={isAlertsLoading || isStatsLoading}
            />
          )}

          {activeTab === 'system' && dashboardData?.system_health && (
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
              {/* CPU Usage */}
              <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                  <div className="flex items-center">
                    <CpuChipIcon className="h-8 w-8 text-blue-500 mr-3" />
                    <div>
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">CPU 사용률</p>
                      <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                        {dashboardData.system_health.cpu_usage_percent.toFixed(1)}%
                      </p>
                    </div>
                  </div>
                  <div className="mt-4">
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          dashboardData.system_health.cpu_usage_percent > 80 ? 'bg-red-500' :
                          dashboardData.system_health.cpu_usage_percent > 60 ? 'bg-yellow-500' : 'bg-green-500'
                        }`}
                        style={{ width: `${dashboardData.system_health.cpu_usage_percent}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Memory Usage */}
              <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                  <div className="flex items-center">
                    <ServerIcon className="h-8 w-8 text-green-500 mr-3" />
                    <div>
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">메모리 사용률</p>
                      <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                        {dashboardData.system_health.memory_usage_percent.toFixed(1)}%
                      </p>
                    </div>
                  </div>
                  <div className="mt-4">
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div 
                        className={`h-2 rounded-full ${
                          dashboardData.system_health.memory_usage_percent > 80 ? 'bg-red-500' :
                          dashboardData.system_health.memory_usage_percent > 60 ? 'bg-yellow-500' : 'bg-green-500'
                        }`}
                        style={{ width: `${dashboardData.system_health.memory_usage_percent}%` }}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Database */}
              <div className="bg-white dark:bg-gray-800 overflow-hidden shadow rounded-lg">
                <div className="px-4 py-5 sm:p-6">
                  <div className="flex items-center">
                    <div className={`h-3 w-3 rounded-full mr-3 ${
                      dashboardData.system_health.postgres_status ? 'bg-green-500' : 'bg-red-500'
                    }`} />
                    <div>
                      <p className="text-sm font-medium text-gray-600 dark:text-gray-400">데이터베이스</p>
                      <p className="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                        {dashboardData.system_health.postgres_status ? '정상' : '오류'}
                      </p>
                    </div>
                  </div>
                  <div className="mt-4 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">연결 수</span>
                      <span className="text-gray-900 dark:text-gray-100">
                        {dashboardData.system_health.db_connection_count}
                      </span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">평균 쿼리 시간</span>
                      <span className="text-gray-900 dark:text-gray-100">
                        {dashboardData.system_health.db_query_avg_time_ms.toFixed(1)}ms
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'logs' && (
            <ErrorLogTable 
              logs={[]} // This would be populated with actual error logs
              onResolve={(id) => console.log('Resolve log:', id)}
              onViewDetails={(log) => console.log('View log details:', log)}
              loading={false}
            />
          )}
        </div>
      </div>
    </Layout>
  );
};

export default MonitoringDashboard;