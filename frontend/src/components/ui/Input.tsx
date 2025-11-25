import React, { useId } from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  fullWidth?: boolean;
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, fullWidth = false, className = '', required, ...props }, ref) => {
    const inputId = useId();
    const errorId = `${inputId}-error`;

    const baseStyles = 'px-4 py-3 bg-white dark:bg-gray-800 border text-gray-900 dark:text-white rounded-lg transition-colors duration-150 focus:outline-none focus:ring-2 disabled:opacity-50 disabled:cursor-not-allowed';

    const borderStyles = error
      ? 'border-red-500 focus:border-red-500 focus:ring-red-500/20'
      : 'border-gray-300 dark:border-gray-600 focus:border-indigo-500 focus:ring-indigo-500/20';

    const widthStyles = fullWidth ? 'w-full' : '';

    const combinedClassName = `${baseStyles} ${borderStyles} ${widthStyles} ${className}`.trim();

    return (
      <div className={fullWidth ? 'w-full' : ''}>
        {label && (
          <label htmlFor={inputId} className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            {label}
            {required && <span className="text-red-500 ml-1" aria-label="필수">*</span>}
          </label>
        )}
        <input
          id={inputId}
          ref={ref}
          required={required}
          aria-invalid={!!error}
          aria-describedby={error ? errorId : undefined}
          aria-required={required}
          className={combinedClassName}
          {...props}
        />
        {error && (
          <p id={errorId} role="alert" className="mt-2 text-sm text-red-600 dark:text-red-400">
            {error}
          </p>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';

export default Input;
