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
  const termsAgreed = watch('terms_agreed');
  const privacyAgreed = watch('privacy_agreed');

  const onSubmit = async (data: RegisterData) => {
    setIsLoading(true);
    setError('');
    setFieldErrors({});
    
    try {
      const response = await registerUser(data);
      
      // Check if email verification is required
      if (response?.data?.requires_email_verification) {
        // Redirect to verification pending page
        navigate(`/verification-pending?email=${encodeURIComponent(data.email)}`);
      } else {
        // Old behavior for backward compatibility
        navigate('/dashboard');
      }
    } catch (err: any) {
      
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
          </div>
          
        </div>

        <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
          <div className="auth-card">
            <div className="auth-card-body">
              <h2 className="text-center text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">
                회원가입
              </h2>
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
                    {fieldErrors.email && (
                      <div className="mt-2 text-sm text-red-600 dark:text-red-400 animate-fadeIn">
                        {fieldErrors.email.map((error, index) => (
                          <p key={index}>{error}</p>
                        ))}
                      </div>
                    )}
                  </div>

                  <div>
                    <label htmlFor="password" className="form-label">
                      비밀번호
                      <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                        (최소 8자 이상)
                      </span>
                    </label>
                    <input
                      {...register('password', { 
                        required: '비밀번호를 입력해주세요.',
                        minLength: { value: 8, message: '비밀번호는 최소 8자 이상이어야 합니다.' }
                      })}
                      type="password"
                      placeholder="••••••••"
                      className="form-input"
                      autoComplete="new-password"
                    />
                    {errors.password && (
                      <p className="mt-2 text-sm text-red-600 dark:text-red-400 animate-fadeIn">
                        {errors.password.message}
                      </p>
                    )}
                    {fieldErrors.password && (
                      <div className="mt-2 text-sm text-red-600 dark:text-red-400 animate-fadeIn">
                        {fieldErrors.password.map((error, index) => (
                          <p key={index}>{error}</p>
                        ))}
                      </div>
                    )}
                  </div>

                  <div>
                    <label htmlFor="password_confirm" className="form-label">
                      비밀번호 확인
                    </label>
                    <input
                      {...register('password_confirm', { 
                        required: '비밀번호 확인을 입력해주세요.',
                        validate: value => value === password || '비밀번호가 일치하지 않습니다.'
                      })}
                      type="password"
                      placeholder="••••••••"
                      className="form-input"
                      autoComplete="new-password"
                    />
                    {errors.password_confirm && (
                      <p className="mt-2 text-sm text-red-600 dark:text-red-400 animate-fadeIn">
                        {errors.password_confirm.message}
                      </p>
                    )}
                  </div>

                  {/* 비밀번호 강도 표시기 */}
                  {password && (
                    <div className="animate-fadeIn">
                      <div className="flex items-center justify-between text-xs mb-1">
                        <span className="text-gray-600 dark:text-gray-400">비밀번호 강도</span>
                        <span className={
                          password.length >= 12 ? 'text-green-600 dark:text-green-400' :
                          password.length >= 8 ? 'text-yellow-600 dark:text-yellow-400' :
                          'text-red-600 dark:text-red-400'
                        }>
                          {password.length >= 12 ? '강함' : password.length >= 8 ? '보통' : '약함'}
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div 
                          className={`h-2 rounded-full transition-all duration-300 ${
                            password.length >= 12 ? 'bg-green-500 w-full' :
                            password.length >= 8 ? 'bg-yellow-500 w-2/3' :
                            'bg-red-500 w-1/3'
                          }`}
                        />
                      </div>
                    </div>
                  )}
                </div>

                {/* 약관 동의 */}
                <div className="space-y-4">
                  <div className="flex items-start">
                    <div className="flex items-center h-5">
                      <input
                        {...register('terms_agreed', {
                          required: '이용약관에 동의해주세요.'
                        })}
                        id="terms_agreed"
                        type="checkbox"
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800"
                      />
                    </div>
                    <div className="ml-3 text-sm">
                      <label htmlFor="terms_agreed" className="text-gray-700 dark:text-gray-300">
                        <Link to="/terms" className="link" target="_blank" rel="noopener noreferrer">
                          이용약관
                        </Link>
                        에 동의합니다. (필수)
                      </label>
                    </div>
                  </div>
                  {errors.terms_agreed && (
                    <p className="text-sm text-red-600 dark:text-red-400 animate-fadeIn ml-7">
                      {errors.terms_agreed.message}
                    </p>
                  )}

                  <div className="flex items-start">
                    <div className="flex items-center h-5">
                      <input
                        {...register('privacy_agreed', {
                          required: '개인정보처리방침에 동의해주세요.'
                        })}
                        id="privacy_agreed"
                        type="checkbox"
                        className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-800"
                      />
                    </div>
                    <div className="ml-3 text-sm">
                      <label htmlFor="privacy_agreed" className="text-gray-700 dark:text-gray-300">
                        <Link to="/privacy" className="link" target="_blank" rel="noopener noreferrer">
                          개인정보처리방침
                        </Link>
                        에 동의합니다. (필수)
                      </label>
                    </div>
                  </div>
                  {errors.privacy_agreed && (
                    <p className="text-sm text-red-600 dark:text-red-400 animate-fadeIn ml-7">
                      {errors.privacy_agreed.message}
                    </p>
                  )}
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
                        계정 생성 중...
                      </div>
                    ) : (
                      '회원가입'
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

              {/* Google Sign In Button */}
              <GoogleSignInButton
                redirectTo="/dashboard"
                onError={(error) => setError(error)}
                buttonText="Google로 회원가입"
                disabled={!termsAgreed || !privacyAgreed}
              />

              {/* Sign In Link */}
              <div className="mt-6 text-center">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  이미 계정이 있으신가요?{' '}
                  <Link to="/login" className="link">
                    로그인하기
                  </Link>
                </p>
              </div>
            </div>
          </div>

        </div>
      </div>
    </>
  
  );
};

export default RegisterPage;