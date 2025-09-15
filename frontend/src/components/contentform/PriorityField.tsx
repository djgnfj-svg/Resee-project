import React from 'react';
import { UseFormRegister } from 'react-hook-form';

interface ContentFormData {
  title: string;
  content: string;
  category?: number;
  priority: 'low' | 'medium' | 'high';
}

interface PriorityFieldProps {
  register: UseFormRegister<ContentFormData>;
  watchedPriority: string;
}

const PriorityField: React.FC<PriorityFieldProps> = ({ register, watchedPriority }) => {
  const priorityOptions = [
    { value: 'high', label: '높음', color: 'red', emoji: '🔴', description: '매우 중요한 내용' },
    { value: 'medium', label: '보통', color: 'yellow', emoji: '🟡', description: '일반적인 내용' },
    { value: 'low', label: '낮음', color: 'green', emoji: '🟢', description: '참고용 내용' }
  ];

  return (
    <div className="space-y-3">
      <label className="block text-sm font-semibold text-gray-900 dark:text-gray-100">
        중요도 <span className="text-red-500">*</span>
      </label>
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {priorityOptions.map((option) => (
          <label key={option.value} className="relative cursor-pointer">
            <input
              {...register('priority', { required: true })}
              type="radio"
              value={option.value}
              className="sr-only"
            />
            <div className={`p-3 rounded-lg border-2 text-center transition-all duration-200 ${
                watchedPriority === option.value
                  ? option.color === 'red'
                    ? 'border-red-400 bg-red-50 dark:bg-red-900/20 ring-2 ring-red-200 dark:ring-red-800'
                    : option.color === 'yellow'
                    ? 'border-yellow-400 bg-yellow-50 dark:bg-yellow-900/20 ring-2 ring-yellow-200 dark:ring-yellow-800'
                    : 'border-green-400 bg-green-50 dark:bg-green-900/20 ring-2 ring-green-200 dark:ring-green-800'
                  : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500 hover:bg-gray-50 dark:hover:bg-gray-700/50'
              }`}>
              <div className="text-xl mb-1">{option.emoji}</div>
              <div className="font-medium text-gray-900 dark:text-gray-100 text-sm">{option.label}</div>
              <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">{option.description}</div>
            </div>
          </label>
        ))}
      </div>
    </div>
  );
};

export default PriorityField;