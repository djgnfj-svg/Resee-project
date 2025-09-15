import React from 'react';
import { UseFormRegister, FieldErrors } from 'react-hook-form';

interface ContentFormData {
  title: string;
  content: string;
  category?: number;
  priority: 'low' | 'medium' | 'high';
}

interface TitleFieldProps {
  register: UseFormRegister<ContentFormData>;
  errors: FieldErrors<ContentFormData>;
  watchedTitle: string;
}

const TitleField: React.FC<TitleFieldProps> = ({ register, errors, watchedTitle }) => {
  return (
    <div className="space-y-3">
      <label className="block text-sm font-semibold text-gray-900 dark:text-gray-100">
        제목 <span className="text-red-500">*</span>
      </label>
      <input
        {...register('title', {
          required: '제목을 입력해주세요.',
          minLength: { value: 3, message: '제목은 최소 3글자 이상이어야 합니다.' }
        })}
        type="text"
        className={`w-full px-4 py-4 text-lg border-2 rounded-xl transition-all duration-200 focus:outline-none bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 ${
          errors.title
            ? 'border-red-300 focus:border-red-500 focus:ring-red-200 dark:border-red-500 dark:focus:border-red-400 dark:focus:ring-red-800'
            : watchedTitle && watchedTitle.trim().length >= 3
            ? 'border-green-300 focus:border-green-500 focus:ring-green-200 dark:border-green-500 dark:focus:border-green-400 dark:focus:ring-green-800'
            : 'border-gray-200 focus:border-indigo-500 focus:ring-indigo-200 dark:border-gray-600 dark:focus:border-indigo-400 dark:focus:ring-indigo-800'
        } focus:ring-4`}
        placeholder="예: React Hook 완벽 가이드"
      />
      {errors.title && (
        <p className="text-sm text-red-600 dark:text-red-400 flex items-center">
          <span className="mr-1">❌</span>
          {errors.title.message}
        </p>
      )}
      {watchedTitle && watchedTitle.trim().length >= 3 && !errors.title && (
        <p className="text-sm text-green-600 dark:text-green-400 flex items-center">
          <span className="mr-1">✅</span>
          좋은 제목이에요!
        </p>
      )}
    </div>
  );
};

export default TitleField;