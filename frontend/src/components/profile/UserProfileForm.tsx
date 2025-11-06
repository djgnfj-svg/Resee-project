import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { authAPI } from '../../utils/api';
import { User } from '../../types';

interface ProfileFormData {
  username?: string;
}

interface UserProfileFormProps {
  user: User;
}

const UserProfileForm: React.FC<UserProfileFormProps> = ({ user }) => {
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);

  // Form setup
  const { register, handleSubmit, reset, formState: { errors, isDirty } } = useForm<ProfileFormData>({
    defaultValues: {
      username: user.username || '',
    },
  });

  // Update form when user data changes
  useEffect(() => {
    reset({
      username: user.username || '',
    });
  }, [user, reset]);

  // Update profile mutation
  const updateProfileMutation = useMutation({
    mutationFn: authAPI.updateProfile,
    onSuccess: (updatedUser) => {
      alert('Success: 프로필이 성공적으로 업데이트되었습니다!');
      queryClient.setQueryData(['profile'], updatedUser);
      setIsEditing(false);
    },
    onError: () => {
      alert('Error: 프로필 업데이트에 실패했습니다.');
    },
  });

  const onSubmit = (data: ProfileFormData) => {
    updateProfileMutation.mutate(data);
  };

  const handleCancel = () => {
    reset({
      username: user.username || '',
    });
    setIsEditing(false);
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg p-6 border border-gray-200 dark:border-gray-700">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">개인 정보</h3>
        {!isEditing ? (
          <button
            onClick={() => setIsEditing(true)}
            className="px-4 py-2 text-sm font-medium text-indigo-600 hover:text-indigo-700 border border-indigo-600 hover:border-indigo-700 rounded-lg transition-colors"
          >
            편집
          </button>
        ) : (
          <div className="flex space-x-2">
            <button
              onClick={handleCancel}
              disabled={updateProfileMutation.isPending}
              className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-700 border border-gray-300 hover:border-gray-400 rounded-lg transition-colors disabled:opacity-50"
            >
              취소
            </button>
            <button
              onClick={handleSubmit(onSubmit)}
              disabled={!isDirty || updateProfileMutation.isPending}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {updateProfileMutation.isPending ? '저장 중...' : '저장'}
            </button>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Email */}
        <div>
          <label htmlFor="email" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            이메일
          </label>
          <input
            type="email"
            id="email"
            value={user.email}
            disabled={true}
            readOnly
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-700 text-gray-500 dark:text-gray-400 cursor-not-allowed"
          />
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            이메일은 로그인 식별자로 사용되며 변경할 수 없습니다.
          </p>
        </div>

        {/* Username */}
        <div>
          <label htmlFor="username" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
            사용자명 (선택사항)
          </label>
          <input
            type="text"
            id="username"
            {...register('username', {
              maxLength: {
                value: 150,
                message: '사용자명은 150자 이하여야 합니다'
              },
              pattern: {
                value: /^[a-zA-Z0-9_-]+$/,
                message: '사용자명은 영문, 숫자, -, _만 사용 가능합니다'
              }
            })}
            disabled={!isEditing}
            placeholder="사용자명을 입력하세요"
            className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-50 dark:disabled:bg-gray-700 disabled:text-gray-500 dark:disabled:text-gray-400 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100"
          />
          {errors.username && (
            <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.username.message}</p>
          )}
          <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
            사용자명은 프로필에 표시되며, 언제든지 변경할 수 있습니다.
          </p>
        </div>
      </form>
    </div>
  );
};

export default UserProfileForm;