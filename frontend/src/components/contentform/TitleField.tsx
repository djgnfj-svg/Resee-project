import React from 'react';
import { UseFormRegister, FieldErrors } from 'react-hook-form';
import { CreateContentData } from '../../types';

type ContentFormData = CreateContentData;

interface TitleFieldProps {
  register: UseFormRegister<ContentFormData>;
  errors: FieldErrors<ContentFormData>;
  watchedTitle: string;
}

const TitleField: React.FC<TitleFieldProps> = ({ register, errors, watchedTitle }) => {
  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8">
      <label className="block text-sm font-medium text-gray-900 dark:text-gray-100 mb-3">
        제목 <span className="text-red-500">*</span>
      </label>
      <input
        {...register('title', {
          required: '제목을 입력해주세요.',
          minLength: { value: 1, message: '제목을 입력해주세요.' }
        })}
        type="text"
        className={`w-full px-3 py-2 text-2xl font-bold border rounded-md transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 ${
          errors.title
            ? 'border-red-300 focus:border-red-500 focus:ring-red-500 dark:border-red-500'
            : watchedTitle && watchedTitle.trim().length >= 1
            ? 'border-gray-300 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:focus:border-blue-400'
            : 'border-gray-300 focus:border-blue-500 focus:ring-blue-500 dark:border-gray-600 dark:focus:border-blue-400'
        }`}
        placeholder="예: React Hook 완벽 가이드"
      />
      {errors.title && (
        <p className="text-sm text-red-600 dark:text-red-400 mt-1">
          {errors.title.message}
        </p>
      )}
    </div>
  );
};

export default TitleField;