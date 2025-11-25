import React from 'react';

/**
 * Loading fallback component for React.lazy Suspense
 * Shows a centered spinner while lazy-loaded components are loading
 */
const LoadingFallback: React.FC = () => {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="flex flex-col items-center gap-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        <p className="text-gray-600 dark:text-gray-400">로딩 중...</p>
      </div>
    </div>
  );
};

export default LoadingFallback;
