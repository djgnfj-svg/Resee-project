import React from 'react';
import { UseFormRegister } from 'react-hook-form';
import { NotificationSettings } from '../../hooks/useNotificationSettings';

interface NotificationToggleProps {
  id: string;
  label: string;
  description: string;
  register: UseFormRegister<NotificationSettings>;
  fieldName: keyof NotificationSettings;
  highlighted?: boolean;
}

const NotificationToggle: React.FC<NotificationToggleProps> = ({
  id,
  label,
  description,
  register,
  fieldName,
  highlighted = false,
}) => {
  const containerClass = highlighted
    ? 'bg-indigo-50 dark:bg-indigo-900/20 p-4 rounded-lg'
    : '';

  const content = (
    <div className="flex items-start space-x-3">
      <div className="flex items-center h-5 mt-0.5">
        <input
          id={id}
          type="checkbox"
          {...register(fieldName as any)}
          className="focus:ring-indigo-500 focus:ring-2 h-4 w-4 text-indigo-600 border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 rounded"
        />
      </div>
      <div className="min-w-0 flex-1">
        <label htmlFor={id} className="block text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </label>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {description}
        </p>
      </div>
    </div>
  );

  return containerClass ? <div className={containerClass}>{content}</div> : content;
};

export default React.memo(NotificationToggle);
