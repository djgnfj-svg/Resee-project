import React from 'react';
import { UseFormSetValue } from 'react-hook-form';
import { NotificationSettings, formatTime, getTimeLabel, hourOptions } from '../../hooks/useNotificationSettings';

interface TimeSelectorProps {
  label: string;
  hour: number;
  onChange: (hour: number) => void;
  setValue: UseFormSetValue<NotificationSettings>;
  fieldName: 'daily_reminder_time' | 'evening_reminder_time' | 'weekly_summary_time';
}

const TimeSelector: React.FC<TimeSelectorProps> = ({
  label,
  hour,
  onChange,
  setValue,
  fieldName,
}) => {
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newHour = parseInt(e.target.value);
    onChange(newHour);
    setValue(fieldName, formatTime(newHour));
  };

  return (
    <div className="ml-7 space-y-2">
      <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
        {label}
      </label>
      <select
        value={hour}
        onChange={handleChange}
        className="px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-indigo-500 focus:border-indigo-500 text-sm shadow-sm min-w-32"
      >
        {hourOptions.map(h => (
          <option key={h} value={h}>
            {getTimeLabel(h)}
          </option>
        ))}
      </select>
    </div>
  );
};

export default React.memo(TimeSelector);
