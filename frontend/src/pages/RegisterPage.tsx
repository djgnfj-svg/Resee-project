import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useAuth } from '../contexts/AuthContext';
import { RegisterData } from '../types';
import GoogleSignInButton from '../components/GoogleSignInButton';

const RegisterPage: React.FC = () => {
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});

  const { register, handleSubmit, watch, formState: { errors } } = useForm<RegisterData>();
  
  const password = watch('password');

  const onSubmit = async (data: RegisterData) => {
    setIsLoading(true);
    setError('');
    setFieldErrors({});
    
    try {
      const response = await registerUser(data);
      
      // Check if email verification is required
      if (response?.requires_email_verification) {
        // Redirect to verification pending page
        navigate(`/verification-pending?email=${encodeURIComponent(data.email)}`);
      } else {
        // Old behavior for backward compatibility
        navigate('/dashboard');
      }
    } catch (err: any) {
      console.error('회원가입 에러:', err.response?.data);
      
      if (err.response?.data?.field_errors) {
        setFieldErrors(err.response.data.field_errors);
        setError(err.response.data.error || '입력 정보를 확인해주세요.');
      } else if (err.response?.data) {
        const errorData = err.response.data;
        const extractedErrors: Record<string, string[]> = {};
        Object.keys(errorData).forEach(field => {
          if (Array.isArray(errorData[field])) {
            extractedErrors[field] = errorData[field];
          } else if (typeof errorData[field] === 'string') {
            extractedErrors[field] = [errorData[field]];
          }
        });
        
        setFieldErrors(extractedErrors);
        setError(errorData.detail || errorData.error || '회원가입에 실패했습니다.');
      } else {
        setError('네트워크 오류가 발생했습니다. 다시 시도해주세요.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-full flex-1 flex-col justify-center px-6 py-12 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-sm">
        <h2 className="mt-10 text-center text-2xl font-bold leading-9 tracking-tight text-gray-900 dark:text-gray-100">
          회원가입
        </h2>
        <p className="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
          회원가입 후 이메일 인증을 완료해주세요
        </p>
      </div>

      <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-sm">
        <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
          {error && (
            <div className="rounded-md bg-red-50 dark:bg-red-900/20 p-4 border border-red-200 dark:border-red-800">
              <div className="text-sm text-red-700 dark:text-red-300">{error}</div>
            </div>
          )}
          
          <div>
            <label htmlFor="email" className="block text-sm font-medium leading-6 text-gray-900 dark:text-gray-100">
              이메일
            </label>
            <div className="mt-2">
              <input
                {...register('email', { 
                  required: '이메일을 입력해주세요.',
                  pattern: {
                    value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                    message: '올바른 이메일 형식을 입력해주세요.'
                  }
                })}
                type="email"
                placeholder="이메일을 입력하세요"
                className="form-input"
              />
              {errors.email && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.email.message}</p>
              )}
              {fieldErrors.email && (
                <div className="mt-1 text-sm text-red-600 dark:text-red-400">
                  {fieldErrors.email.map((error, index) => (
                    <p key={index}>{error}</p>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium leading-6 text-gray-900 dark:text-gray-100">
              비밀번호
            </label>
            <div className="mt-2">
              <input
                {...register('password', { 
                  required: '비밀번호를 입력해주세요.',
                  minLength: { value: 8, message: '비밀번호는 최소 8자 이상이어야 합니다.' }
                })}
                type="password"
                placeholder="비밀번호를 입력하세요"
                className="form-input"
              />
              {errors.password && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.password.message}</p>
              )}
              {fieldErrors.password && (
                <div className="mt-1 text-sm text-red-600 dark:text-red-400">
                  {fieldErrors.password.map((error, index) => (
                    <p key={index}>{error}</p>
                  ))}
                </div>
              )}
            </div>
          </div>

          <div>
            <label htmlFor="password_confirm" className="block text-sm font-medium leading-6 text-gray-900 dark:text-gray-100">
              비밀번호 확인
            </label>
            <div className="mt-2">
              <input
                {...register('password_confirm', { 
                  required: '비밀번호 확인을 입력해주세요.',
                  validate: value => value === password || '비밀번호가 일치하지 않습니다.'
                })}
                type="password"
                placeholder="비밀번호를 다시 입력하세요"
                className="form-input"
              />
              {errors.password_confirm && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.password_confirm.message}</p>
              )}
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="btn btn-primary btn-md w-full"
            >
              {isLoading ? '계정 생성 중...' : '회원가입'}
            </button>
          </div>
        </form>

        {/* Social Login Section - only show if Google OAuth is configured */}
        {process.env.REACT_APP_GOOGLE_CLIENT_ID && (
          <>
            {/* Social Login Divider */}
            <div className="mt-6">
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300 dark:border-gray-600" />
                </div>
                <div className="relative flex justify-center text-sm font-medium leading-6">
                  <span className="bg-white dark:bg-gray-900 px-6 text-gray-900 dark:text-gray-100">또는</span>
                </div>
              </div>
            </div>

            {/* Google Sign In */}
            <div className="mt-6">
              <GoogleSignInButton
                onSuccess={() => navigate('/dashboard')}
                onError={(error) => setError(error)}
              />
            </div>
          </>
        )}

        <p className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
          이미 계정이 있으신가요?{' '}
          <Link to="/login" className="font-semibold leading-6 text-primary-600 hover:text-primary-500">
            로그인
          </Link>
        </p>
      </div>
    </div>
  );
};

export default RegisterPage;