import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useAuth } from '../contexts/AuthContext';
import { LoginData } from '../types';
import GoogleSignInButton from '../components/GoogleSignInButton';

const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showEmailVerificationLink, setShowEmailVerificationLink] = useState(false);
  const [userEmail, setUserEmail] = useState('');

  const { register, handleSubmit, formState: { errors } } = useForm<LoginData>();

  const from = location.state?.from?.pathname || '/dashboard';

  const onSubmit = async (data: LoginData) => {
    setIsLoading(true);
    setError('');
    setShowEmailVerificationLink(false);
    
    try {
      await login(data);
      navigate(from, { replace: true });
    } catch (err: any) {
      // Use userMessage from API interceptor if available
      let errorMessage = err.userMessage;
      
      if (!errorMessage) {
        // Fallback error handling in case interceptor didn't process it
        if (err.response?.data?.non_field_errors && Array.isArray(err.response.data.non_field_errors)) {
          errorMessage = err.response.data.non_field_errors[0];
        } else if (err.response?.data?.detail) {
          errorMessage = err.response.data.detail;
        } else if (err.response?.data?.message) {
          errorMessage = err.response.data.message;
        } else {
          errorMessage = '로그인에 실패했습니다.';
        }
      }
      
      // Check if the error is related to email verification
      if (errorMessage.includes('이메일 인증')) {
        setShowEmailVerificationLink(true);
        setUserEmail(data.email);
      }
      
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleResendVerification = () => {
    navigate(`/verification-pending?email=${encodeURIComponent(userEmail)}`);
  };

  return (
    <div className="flex min-h-full flex-1 flex-col justify-center px-6 py-12 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-sm">
        <h2 className="mt-10 text-center text-2xl font-bold leading-9 tracking-tight text-gray-900 dark:text-gray-100">
          로그인
        </h2>
      </div>

      <div className="mt-10 sm:mx-auto sm:w-full sm:max-w-sm">
        <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
          {error && (
            <div className="rounded-md bg-red-50 dark:bg-red-900/20 p-4 border border-red-200 dark:border-red-800">
              <div className="text-sm text-red-700 dark:text-red-300">{error}</div>
              {showEmailVerificationLink && (
                <div className="mt-3">
                  <button
                    type="button"
                    onClick={handleResendVerification}
                    className="text-sm text-indigo-600 hover:text-indigo-500 font-medium underline"
                  >
                    인증 이메일 재발송하기
                  </button>
                </div>
              )}
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
                className="block w-full rounded-md border-0 py-1.5 text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-800 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-600 placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:ring-2 focus:ring-inset focus:ring-primary-600 sm:text-sm sm:leading-6"
              />
              {errors.email && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.email.message}</p>
              )}
            </div>
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium leading-6 text-gray-900 dark:text-gray-100">
              비밀번호
            </label>
            <div className="mt-2">
              <input
                {...register('password', { required: '비밀번호를 입력해주세요.' })}
                type="password"
                className="block w-full rounded-md border-0 py-1.5 text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-800 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-600 placeholder:text-gray-400 dark:placeholder:text-gray-500 focus:ring-2 focus:ring-inset focus:ring-primary-600 sm:text-sm sm:leading-6"
              />
              {errors.password && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.password.message}</p>
              )}
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="flex w-full justify-center rounded-md bg-primary-600 px-3 py-1.5 text-sm font-semibold leading-6 text-white shadow-sm hover:bg-primary-500 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-primary-600 disabled:opacity-50"
            >
              {isLoading ? '로그인 중...' : '로그인'}
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
                onSuccess={() => navigate(from, { replace: true })}
                onError={(error) => setError(error)}
                redirectTo={from}
              />
            </div>
          </>
        )}


        <p className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
          계정이 없으신가요?{' '}
          <Link to="/register" className="font-semibold leading-6 text-primary-600 hover:text-primary-500">
            회원가입
          </Link>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;