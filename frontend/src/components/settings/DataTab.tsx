import React from 'react';
import { useForm } from 'react-hook-form';
import { useMutation } from '@tanstack/react-query';
import { authAPI } from '../../utils/api';

const DataTab: React.FC = () => {
  const deleteAccountForm = useForm<{ password: string; confirmation: string }>({
    defaultValues: {
      password: '',
      confirmation: '',
    },
  });

  const deleteAccountMutation = useMutation({
    mutationFn: authAPI.deleteAccount,
    onSuccess: () => {
      alert('Success: 계정이 성공적으로 삭제되었습니다.');
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      window.location.href = '/login';
    },
    onError: (error: any) => {
      const errorMessage = error.response?.data?.password || error.response?.data?.confirmation || '계정 삭제에 실패했습니다.';
      alert('Error: ' + errorMessage);
    },
  });

  const exportData = () => {
    alert('Success: 데이터 내보내기가 시작되었습니다. 이메일로 다운로드 링크를 보내드릴게요.');
  };

  const onDeleteAccount = (data: { password: string; confirmation: string }) => {
    if (data.confirmation !== 'DELETE') {
      alert('Error: "DELETE"를 정확히 입력해주세요.');
      return;
    }
    deleteAccountMutation.mutate(data);
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-4">데이터 관리</h3>

        <div className="space-y-4">
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-base font-medium text-gray-900">데이터 내보내기</h4>
                <p className="text-sm text-gray-600">
                  모든 학습 데이터를 JSON 형식으로 내보냅니다.
                </p>
              </div>
              <button
                onClick={exportData}
                className="bg-green-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
              >
                내보내기
              </button>
            </div>
          </div>

          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between">
              <div>
                <h4 className="text-base font-medium text-gray-900">데이터 가져오기</h4>
                <p className="text-sm text-gray-600">
                  이전에 내보낸 데이터를 가져옵니다.
                </p>
              </div>
              <button
                disabled
                className="bg-gray-300 text-gray-500 px-4 py-2 rounded-md text-sm font-medium cursor-not-allowed"
              >
                준비 중
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="border-t border-gray-200 pt-6">
        <h3 className="text-lg font-medium text-red-600 mb-4">위험 영역</h3>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="mb-4">
            <h4 className="text-base font-medium text-red-900">계정 삭제</h4>
            <p className="text-sm text-red-700">
              모든 데이터가 영구적으로 삭제됩니다. 이 작업은 되돌릴 수 없습니다.
            </p>
          </div>

          <form onSubmit={deleteAccountForm.handleSubmit(onDeleteAccount)} className="space-y-4">
            <div>
              <label htmlFor="delete_password" className="block text-sm font-medium text-red-700 mb-2">
                계정 삭제를 위해 비밀번호를 입력해주세요
              </label>
              <input
                type="password"
                id="delete_password"
                {...deleteAccountForm.register('password', { required: '비밀번호를 입력해주세요' })}
                className="w-full px-3 py-2 border border-red-300 rounded-md focus:ring-red-500 focus:border-red-500"
                placeholder="비밀번호"
              />
            </div>

            <div>
              <label htmlFor="delete_confirmation" className="block text-sm font-medium text-red-700 mb-2">
                계정 삭제를 확인하기 위해 "DELETE"를 입력해주세요
              </label>
              <input
                type="text"
                id="delete_confirmation"
                {...deleteAccountForm.register('confirmation', { required: '"DELETE"를 입력해주세요' })}
                className="w-full px-3 py-2 border border-red-300 rounded-md focus:ring-red-500 focus:border-red-500"
                placeholder="DELETE"
              />
            </div>

            <div className="pt-2">
              <button
                type="submit"
                disabled={deleteAccountMutation.isPending}
                className="bg-red-600 text-white px-4 py-2 rounded-md text-sm font-medium hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 disabled:opacity-50"
              >
                {deleteAccountMutation.isPending ? '삭제 중...' : '계정 영구 삭제'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default DataTab;