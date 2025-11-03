import React from 'react';
import { ValidationResult } from '../../hooks/useContentValidation';

interface ValidationResultCardProps {
  result: ValidationResult;
}

const ValidationResultCard: React.FC<ValidationResultCardProps> = ({ result }) => {
  const renderMetric = (
    label: string,
    score: number,
    issues: string[],
    color: 'blue' | 'purple' | 'green'
  ) => {
    const colorClasses = {
      blue: {
        text: 'text-indigo-600 dark:text-indigo-400',
        bg: 'bg-gradient-to-r from-indigo-500 to-purple-600',
      },
      purple: {
        text: 'text-purple-600 dark:text-purple-400',
        bg: 'bg-gradient-to-r from-purple-500 to-purple-600',
      },
      green: {
        text: 'text-green-600 dark:text-green-400',
        bg: 'bg-gradient-to-r from-green-500 to-green-600',
      },
    };

    return (
      <div>
        <div className="flex justify-between items-center mb-1">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{label}</span>
          <span className={`text-sm font-bold ${colorClasses[color].text}`}>{score}점</span>
        </div>
        <div className="h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
          <div
            className={`h-full ${colorClasses[color].bg} transition-all duration-500`}
            style={{ width: `${score}%` }}
          />
        </div>
        {issues.length > 0 && (
          <ul className="mt-1 text-xs text-red-600 dark:text-red-400 list-disc list-inside">
            {issues.map((issue, i) => (
              <li key={i}>{issue}</li>
            ))}
          </ul>
        )}
      </div>
    );
  };

  return (
    <div className="mt-4 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/20 dark:to-purple-900/20 border-2 border-indigo-200 dark:border-indigo-700 rounded-xl p-6">
      <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
        AI 검증 결과 {result.is_valid ? '✓' : '⚠️'}
      </h3>

      <div className="space-y-3 mb-4">
        {renderMetric('사실적 정확성', result.factual_accuracy.score, result.factual_accuracy.issues, 'blue')}
        {renderMetric('논리적 일관성', result.logical_consistency.score, result.logical_consistency.issues, 'purple')}
        {renderMetric('제목 적합성', result.title_relevance.score, result.title_relevance.issues, 'green')}
      </div>

      <p className="text-sm text-gray-700 dark:text-gray-300 leading-relaxed">
        {result.overall_feedback}
      </p>
    </div>
  );
};

export default ValidationResultCard;
