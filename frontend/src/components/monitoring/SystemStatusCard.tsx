import React from 'react';
import { 
  ArrowTrendingUpIcon, 
  ArrowTrendingDownIcon,
  MinusIcon 
} from '@heroicons/react/24/outline';
import { LoadingSpinner } from '../LoadingSpinner';
import type { SystemStatusCardProps } from '../../types/monitoring';

export const SystemStatusCard: React.FC<SystemStatusCardProps> = ({
  title,
  value,
  unit = '',
  status,
  trend,
  loading = false,
  onClick,
  icon
}) => {
  const getStatusColor = () => {
    switch (status) {
      case 'healthy':
        return 'text-green-600 dark:text-green-400';
      case 'warning':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'critical':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getStatusBgColor = () => {
    switch (status) {
      case 'healthy':
        return 'bg-green-50 dark:bg-green-900/20';
      case 'warning':
        return 'bg-yellow-50 dark:bg-yellow-900/20';
      case 'critical':
        return 'bg-red-50 dark:bg-red-900/20';
      default:
        return 'bg-gray-50 dark:bg-gray-800';
    }
  };

  const getTrendIcon = () => {
    switch (trend) {
      case 'up':
        return <ArrowTrendingUpIcon className="h-4 w-4 text-green-500" />;
      case 'down':
        return <ArrowTrendingDownIcon className="h-4 w-4 text-red-500" />;
      case 'stable':
        return <MinusIcon className="h-4 w-4 text-gray-400" />;
      default:
        return null;
    }
  };

  const formatValue = (val: number | string) => {
    if (typeof val === 'number') {
      // Format numbers with appropriate precision
      if (val >= 1000) {
        return (val / 1000).toFixed(1) + 'K';
      }
      if (val % 1 === 0) {
        return val.toString();
      }
      return val.toFixed(1);
    }
    return val;
  };

  return (
    <div 
      className={`${getStatusBgColor()} overflow-hidden rounded-lg border border-gray-200 dark:border-gray-700 shadow transition-all duration-200 ${
        onClick ? 'cursor-pointer hover:shadow-md' : ''
      }`}
      onClick={onClick}
    >
      <div className="px-4 py-5 sm:p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className={`${getStatusColor()} opacity-75`}>
              {icon}
            </div>
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-600 dark:text-gray-400 truncate">
                {title}
              </dt>
              <dd className="flex items-baseline">
                {loading ? (
                  <LoadingSpinner size="small" />
                ) : (
                  <>
                    <div className={`text-2xl font-semibold ${getStatusColor()}`}>
                      {formatValue(value)}
                      {unit && <span className="text-lg ml-1">{unit}</span>}
                    </div>
                    {trend && (
                      <div className="ml-2 flex items-baseline text-sm">
                        {getTrendIcon()}
                      </div>
                    )}
                  </>
                )}
              </dd>
            </dl>
          </div>
        </div>
        
        {status === 'critical' && (
          <div className="mt-3">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="h-2 w-2 bg-red-500 rounded-full animate-pulse"></div>
              </div>
              <div className="ml-2 text-xs text-red-600 dark:text-red-400">
                즉시 확인 필요
              </div>
            </div>
          </div>
        )}
        
        {status === 'warning' && (
          <div className="mt-3">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="h-2 w-2 bg-yellow-500 rounded-full"></div>
              </div>
              <div className="ml-2 text-xs text-yellow-600 dark:text-yellow-400">
                주의 필요
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};