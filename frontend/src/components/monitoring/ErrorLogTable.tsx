import React, { useState } from 'react';
import { 
  ExclamationTriangleIcon,
  XCircleIcon,
  CheckCircleIcon,
  EyeIcon
} from '@heroicons/react/24/outline';
import { LoadingSpinner } from '../LoadingSpinner';
import type { ErrorLogTableProps, ErrorLog } from '../../types/monitoring';

export const ErrorLogTable: React.FC<ErrorLogTableProps> = ({
  logs,
  onResolve,
  onViewDetails,
  loading = false
}) => {
  const [selectedLogs, setSelectedLogs] = useState<number[]>([]);

  const getLevelIcon = (level: string) => {
    switch (level) {
      case 'CRITICAL':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'ERROR':
        return <ExclamationTriangleIcon className="h-5 w-5 text-orange-500" />;
      case 'WARNING':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      default:
        return <ExclamationTriangleIcon className="h-5 w-5 text-gray-500" />;
    }
  };

  const getLevelBadge = (level: string) => {
    const baseClasses = "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium";
    
    switch (level) {
      case 'CRITICAL':
        return `${baseClasses} bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200`;
      case 'ERROR':
        return `${baseClasses} bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200`;
      case 'WARNING':
        return `${baseClasses} bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200`;
      default:
        return `${baseClasses} bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200`;
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString('ko-KR');
  };

  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedLogs(logs.filter(log => !log.resolved).map(log => log.id));
    } else {
      setSelectedLogs([]);
    }
  };

  const handleSelectLog = (logId: number, checked: boolean) => {
    if (checked) {
      setSelectedLogs(prev => [...prev, logId]);
    } else {
      setSelectedLogs(prev => prev.filter(id => id !== logId));
    }
  };

  const handleBulkResolve = () => {
    selectedLogs.forEach(logId => onResolve(logId));
    setSelectedLogs([]);
  };

  if (loading) {
    return (
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center justify-center h-64">
            <LoadingSpinner size="large" />
          </div>
        </div>
      </div>
    );
  }

  if (!logs || logs.length === 0) {
    return (
      <div className="bg-white dark:bg-gray-800 shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="text-center py-12">
            <CheckCircleIcon className="mx-auto h-12 w-12 text-green-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-gray-100">
              에러 로그가 없습니다
            </h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              현재 시스템에 에러가 없습니다. 좋은 상태입니다!
            </p>
          </div>
        </div>
      </div>
    );
  }

  const unresolvedLogs = logs.filter(log => !log.resolved);
  const hasUnresolvedLogs = unresolvedLogs.length > 0;

  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
      {/* Header */}
      <div className="px-4 py-5 sm:px-6 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg leading-6 font-medium text-gray-900 dark:text-gray-100">
              에러 로그
            </h3>
            <p className="mt-1 max-w-2xl text-sm text-gray-500 dark:text-gray-400">
              시스템에서 발생한 에러 로그를 확인하고 관리할 수 있습니다.
            </p>
          </div>
          {selectedLogs.length > 0 && (
            <button
              onClick={handleBulkResolve}
              className="inline-flex items-center px-3 py-2 border border-transparent text-sm leading-4 font-medium rounded-md text-white bg-green-600 hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-green-500"
            >
              <CheckCircleIcon className="h-4 w-4 mr-2" />
              선택된 로그 해결 ({selectedLogs.length})
            </button>
          )}
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-900">
            <tr>
              <th className="px-6 py-3 text-left">
                <input
                  type="checkbox"
                  className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                  checked={hasUnresolvedLogs && selectedLogs.length === unresolvedLogs.length}
                  onChange={(e) => handleSelectAll(e.target.checked)}
                  disabled={!hasUnresolvedLogs}
                />
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                레벨
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                메시지
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                엔드포인트
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                발생 횟수
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                시간
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                상태
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-300 uppercase tracking-wider">
                액션
              </th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
            {logs.map((log) => (
              <tr 
                key={log.id}
                className={`${log.resolved ? 'opacity-60' : ''} hover:bg-gray-50 dark:hover:bg-gray-700`}
              >
                <td className="px-6 py-4 whitespace-nowrap">
                  <input
                    type="checkbox"
                    className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                    checked={selectedLogs.includes(log.id)}
                    onChange={(e) => handleSelectLog(log.id, e.target.checked)}
                    disabled={log.resolved}
                  />
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="flex items-center">
                    {getLevelIcon(log.level)}
                    <span className={`ml-2 ${getLevelBadge(log.level)}`}>
                      {log.level}
                    </span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  <div className="text-sm text-gray-900 dark:text-gray-100 max-w-md">
                    <p className="truncate" title={log.message}>
                      {log.message}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {log.exception_type}
                    </p>
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 dark:text-gray-100">
                  {log.endpoint || '-'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200">
                    {log.occurrences}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500 dark:text-gray-400">
                  {formatTimestamp(log.timestamp)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  {log.resolved ? (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                      <CheckCircleIcon className="h-3 w-3 mr-1" />
                      해결됨
                    </span>
                  ) : (
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                      <ExclamationTriangleIcon className="h-3 w-3 mr-1" />
                      미해결
                    </span>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium space-x-2">
                  <button
                    onClick={() => onViewDetails(log)}
                    className="text-blue-600 hover:text-blue-900 dark:text-blue-400 dark:hover:text-blue-300"
                  >
                    <EyeIcon className="h-4 w-4" />
                  </button>
                  {!log.resolved && (
                    <button
                      onClick={() => onResolve(log.id)}
                      className="text-green-600 hover:text-green-900 dark:text-green-400 dark:hover:text-green-300"
                    >
                      <CheckCircleIcon className="h-4 w-4" />
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="px-4 py-3 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-700 dark:text-gray-300">
            총 <span className="font-medium">{logs.length}</span>개의 로그, 
            <span className="font-medium text-red-600 dark:text-red-400 ml-1">
              {unresolvedLogs.length}
            </span>개 미해결
          </div>
        </div>
      </div>
    </div>
  );
};