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

              {/* Social Login Section - only show if Google OAuth is configured */}
              {process.env.REACT_APP_GOOGLE_CLIENT_ID && (
                <>
                  {/* Divider */}
                  <div className="divider">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-gray-300 dark:border-gray-600" />
                    </div>
                    <div className="divider-text">
                      <span>또는</span>
                    </div>
                  </div>

                  {/* Google Sign In */}
                  <div>
                    <GoogleSignInButton
                      onSuccess={() => navigate(from, { replace: true })}
                      onError={(error) => setError(error)}
                      redirectTo={from}
                    />
                  </div>
                </>
              )}

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