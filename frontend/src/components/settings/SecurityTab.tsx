import React from 'react';
import { useForm } from 'react-hook-form';
import { useMutation } from '@tanstack/react-query';
import { authAPI } from '../../utils/api';

interface SecuritySettings {
  current_password: string;
  new_password: string;
  confirm_password: string;
}

const SecurityTab: React.FC = () => {
  const securityForm = useForm<SecuritySettings>({
    defaultValues: {
      current_password: '',
      new_password: '',
      confirm_password: '',
    },
  });

  const changePasswordMutation = useMutation({
    mutationFn: authAPI.changePassword,
    onSuccess: () => {
      alert('Success: 비밀번호가 성공적으로 변경되었습니다!');
      securityForm.reset();
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.current_password || error.response?.data?.new_password || '비밀번호 변경에 실패했습니다.';
      alert('Error: ' + errorMessage);
    },
  });

  const onSecuritySubmit = (data: SecuritySettings) => {
    if (data.new_password !== data.confirm_password) {
      alert('Error: 새 비밀번호가 일치하지 않습니다.');
      return;
    }
    changePasswordMutation.mutate({
      current_password: data.current_password,
      new_password: data.new_password,
      new_password_confirm: data.confirm_password,
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">비밀번호 변경</h3>
        <form onSubmit={securityForm.handleSubmit(onSecuritySubmit)} className="space-y-4">
          <div>
            <label htmlFor="current_password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              현재 비밀번호
            </label>
            <input
              type="password"
              id="current_password"
              {...securityForm.register('current_password', { required: '현재 비밀번호를 입력해주세요' })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label htmlFor="new_password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              새 비밀번호
            </label>
            <input
              type="password"
              id="new_password"
              {...securityForm.register('new_password', {
                required: '새 비밀번호를 입력해주세요',
                minLength: { value: 8, message: '비밀번호는 최소 8자 이상이어야 합니다' }
              })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div>
            <label htmlFor="confirm_password" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              새 비밀번호 확인
            </label>
            <input
              type="password"
              id="confirm_password"
              {...securityForm.register('confirm_password', { required: '비밀번호 확인을 입력해주세요' })}
              className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-md focus:ring-blue-500 focus:border-blue-500"
            />
          </div>

          <div className="pt-4">
            <button
              type="submit"
              disabled={changePasswordMutation.isPending}
              className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 dark:focus:ring-offset-gray-800 disabled:opacity-50"
            >
              {changePasswordMutation.isPending ? '변경 중...' : '비밀번호 변경'}
            </button>
          </div>
        </form>
      </div>

      <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
        <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100 mb-4">보안 정보</h3>
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400 dark:text-blue-300" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800 dark:text-blue-200">보안 팁</h3>
              <div className="mt-2 text-sm text-blue-700 dark:text-blue-300">
                <ul className="list-disc pl-5 space-y-1">
                  <li>강력한 비밀번호를 사용하세요 (대소문자, 숫자, 특수문자 포함)</li>
                  <li>정기적으로 비밀번호를 변경하세요</li>
                  <li>다른 사이트와 같은 비밀번호를 사용하지 마세요</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SecurityTab;