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
      // Check if email verification is required first
      if (err.response?.data?.email_verification_required) {
        const email = err.response.data.email || data.email;
        navigate(`/verification-pending?email=${encodeURIComponent(email)}`);
        return;
      }
      
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
      
      // Check if the error is related to email verification (fallback)
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
    <>
      {/* Background Pattern */}
      <div className="auth-bg-pattern" />
      
      <div className="relative flex min-h-screen flex-col justify-center px-6 py-12 lg:px-8">
        <div className="sm:mx-auto sm:w-full sm:max-w-md">
          {/* Logo and Title */}
          <div className="text-center">
            <Link to="/" className="inline-block">
              <h1 className="text-4xl font-bold gradient-text mb-2">Resee</h1>
            </Link>
            <p className="text-sm text-gray-600 dark:text-gray-400">과학적 복습 플랫폼</p>
          </div>
          
          <h2 className="mt-8 text-center text-3xl font-extrabold text-gray-900 dark:text-gray-100">
            다시 만나서 반가워요!
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600 dark:text-gray-400">
            학습을 계속하려면 로그인하세요
          </p>
        </div>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="auth-card">
            <div className="auth-card-body">
              <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
                {error && (
                  <div className="alert alert-error animate-fadeIn">
                    <div className="flex">
                      <div className="flex-shrink-0">
                        <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                      </div>
                      <div className="ml-3">
                        <p className="text-sm">{error}</p>
                        {showEmailVerificationLink && (
                          <div className="mt-2">
                            <button
                              type="button"
                              onClick={handleResendVerification}
                              className="text-sm link"
                            >
                              인증 이메일 재발송하기
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                )}
                
                <div className="space-y-5">
                  <div>
                    <label htmlFor="email" className="form-label">
                      이메일
                    </label>
                    <input
                      {...register('email', { 
                        required: '이메일을 입력해주세요.',
                        pattern: {
                          value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                          message: '올바른 이메일 형식을 입력해주세요.'
                        }
                      })}
                      type="email"
                      placeholder="name@example.com"
                      className="form-input"
                      autoComplete="email"
                    />
                    {errors.email && (
                      <p className="mt-2 text-sm text-red-600 dark:text-red-400 animate-fadeIn">
                        {errors.email.message}
                      </p>
                    )}
                  </div>

                  <div>
                    <label htmlFor="password" className="form-label">
                      비밀번호
                    </label>
                    <input
                      {...register('password', { required: '비밀번호를 입력해주세요.' })}
                      type="password"
                      placeholder="••••••••"
                      className="form-input"
                      autoComplete="current-password"
                    />
                    {errors.password && (
                      <p className="mt-2 text-sm text-red-600 dark:text-red-400 animate-fadeIn">
                        {errors.password.message}
                      </p>
                    )}
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={isLoading}
                    className="btn btn-primary btn-lg w-full relative"
                  >
                    {isLoading ? (
                      <div className="flex items-center justify-center">
                        <div className="spinner mr-2" />
                        로그인 중...
                      </div>
                    ) : (
                      '로그인'
                    )}
                  </button>
                </div>
              </form>

              {/* Google Sign In - Coming Soon */}
              {/* Divider */}
              <div className="divider">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-gray-300 dark:border-gray-600" />
                </div>
                <div className="divider-text">
                  <span>또는</span>
                </div>
              </div>

              {/* Google Sign In Button - Coming Soon */}
              <button
                type="button"
                onClick={() => alert('🚀 곧 출시됩니다!\n\nGoogle 로그인 기능은 현재 개발 중입니다.\n잠시만 기다려주세요!')}
                className="w-full flex items-center justify-center px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors cursor-pointer"
              >
                <svg className="w-5 h-5 mr-3" viewBox="0 0 24 24">
                  <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Google로 로그인 (준비중)
              </button>

              {/* Sign Up Link */}
              <div className="mt-6 text-center">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  아직 계정이 없으신가요?{' '}
                  <Link to="/register" className="link">
                    무료로 가입하기
                  </Link>
                </p>
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="mt-8 text-center">
            <p className="text-xs text-gray-500 dark:text-gray-400">
              로그인하면 Resee의{' '}
              <a href="#" className="hover:text-gray-700 dark:hover:text-gray-300">
                이용약관
              </a>
              {' '}및{' '}
              <a href="#" className="hover:text-gray-700 dark:hover:text-gray-300">
                개인정보처리방침
              </a>
              에 동의하는 것으로 간주됩니다.
            </p>
          </div>
        </div>
      </div>
    </>
  
  );
};

export default LoginPage;