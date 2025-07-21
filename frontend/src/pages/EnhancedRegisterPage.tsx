import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { useAuth } from '../contexts/AuthContext';
import { RegisterData } from '../types';
import PasswordStrengthMeter from '../components/PasswordStrengthMeter';
import {
  UserIcon,
  EnvelopeIcon,
  LockClosedIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

const EnhancedRegisterPage: React.FC = () => {
  const { register: registerUser } = useAuth();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string[]>>({});
  const [showPassword, setShowPassword] = useState(false);
  const [step, setStep] = useState(1); // 다단계 폼

  const { register, handleSubmit, watch, formState: { errors, isValid } } = useForm<RegisterData>({
    mode: 'onChange', // 실시간 유효성 검사
  });
  
  const password = watch('password');
  const email = watch('email');
  const firstName = watch('first_name');
  const lastName = watch('last_name');

  const onSubmit = async (data: RegisterData) => {
    setIsLoading(true);
    setError('');
    setFieldErrors({});
    
    try {
      await registerUser(data);
      // 성공 시 대시보드로 이동 (AuthContext에서 welcome modal 표시)
      navigate('/dashboard');
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

  const nextStep = () => {
    if (step < 3) setStep(step + 1);
  };

  const prevStep = () => {
    if (step > 1) setStep(step - 1);
  };

  // 단계별 유효성 검사
  const isStepValid = (stepNumber: number) => {
    switch (stepNumber) {
      case 1:
        return email && /^\S+@\S+$/i.test(email);
      case 2:
        return password && password.length >= 8 && /[a-zA-Z]/.test(password) && /\d/.test(password);
      case 3:
        return firstName && lastName;
      default:
        return false;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* 헤더 */}
        <div className="text-center">
          <div className="mx-auto h-12 w-12 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mb-4">
            <SparklesIcon className="h-6 w-6 text-white" />
          </div>
          <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            Resee와 함께 시작하세요
          </h2>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            과학적인 복습으로 효과적인 학습을 경험해보세요
          </p>
        </div>

        {/* 진행 상태 표시 */}
        <div className="flex justify-center">
          <div className="flex items-center space-x-4">
            {[1, 2, 3].map((stepNumber) => (
              <React.Fragment key={stepNumber}>
                <div
                  className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium transition-all duration-300 ${
                    step >= stepNumber
                      ? 'bg-blue-500 text-white shadow-lg'
                      : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
                  }`}
                >
                  {step > stepNumber ? (
                    <CheckCircleIcon className="w-5 h-5" />
                  ) : (
                    stepNumber
                  )}
                </div>
                {stepNumber < 3 && (
                  <div
                    className={`w-8 h-0.5 transition-all duration-300 ${
                      step > stepNumber ? 'bg-blue-500' : 'bg-gray-200 dark:bg-gray-700'
                    }`}
                  />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* 폼 카드 */}
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl p-8 border border-gray-200 dark:border-gray-700">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* 에러 메시지 */}
            {error && (
              <div className="rounded-lg bg-red-50 dark:bg-red-900/20 p-4 border border-red-200 dark:border-red-800 animate-bounce-in">
                <div className="flex">
                  <ExclamationTriangleIcon className="h-5 w-5 text-red-400 mr-2" />
                  <div className="text-sm text-red-700 dark:text-red-300">{error}</div>
                </div>
              </div>
            )}

            {/* 1단계: 이메일 */}
            {step === 1 && (
              <div className="space-y-4 animate-slide-in">
                <div className="text-center">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    이메일 주소를 입력해주세요
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    로그인에 사용될 이메일 주소입니다
                  </p>
                </div>

                <div className="relative">
                  <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <EnvelopeIcon className="h-5 w-5 text-gray-400" />
                  </div>
                  <input
                    {...register('email', { 
                      required: '이메일을 입력해주세요.',
                      pattern: { value: /^\S+@\S+$/i, message: '올바른 이메일 형식을 입력해주세요.' }
                    })}
                    type="email"
                    placeholder="이메일 주소"
                    className="block w-full pl-10 pr-3 py-3 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-gray-100 text-lg"
                  />
                  {email && /^\S+@\S+$/i.test(email) && (
                    <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                      <CheckCircleIcon className="h-5 w-5 text-green-500" />
                    </div>
                  )}
                </div>
                {errors.email && (
                  <p className="text-sm text-red-600 dark:text-red-400">{errors.email.message}</p>
                )}
                {fieldErrors.email && (
                  <div className="text-sm text-red-600 dark:text-red-400">
                    {fieldErrors.email.map((error, index) => (
                      <p key={index}>{error}</p>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* 2단계: 비밀번호 */}
            {step === 2 && (
              <div className="space-y-4 animate-slide-in">
                <div className="text-center">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    안전한 비밀번호를 설정하세요
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    계정 보안을 위해 강력한 비밀번호를 만들어주세요
                  </p>
                </div>

                <div className="space-y-4">
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <LockClosedIcon className="h-5 w-5 text-gray-400" />
                    </div>
                    <input
                      {...register('password', { 
                        required: '비밀번호를 입력해주세요.',
                        minLength: { value: 8, message: '비밀번호는 최소 8자 이상이어야 합니다.' }
                      })}
                      type={showPassword ? 'text' : 'password'}
                      placeholder="비밀번호"
                      className="block w-full pl-10 pr-3 py-3 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-gray-100"
                    />
                  </div>

                  {/* 비밀번호 강도 표시기 */}
                  <PasswordStrengthMeter 
                    password={password || ''} 
                    showPassword={showPassword}
                    onToggleVisibility={() => setShowPassword(!showPassword)}
                  />

                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <LockClosedIcon className="h-5 w-5 text-gray-400" />
                    </div>
                    <input
                      {...register('password_confirm', { 
                        required: '비밀번호 확인을 입력해주세요.',
                        validate: value => value === password || '비밀번호가 일치하지 않습니다.'
                      })}
                      type="password"
                      placeholder="비밀번호 확인"
                      className="block w-full pl-10 pr-3 py-3 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-gray-100"
                    />
                  </div>
                  {errors.password_confirm && (
                    <p className="text-sm text-red-600 dark:text-red-400">{errors.password_confirm.message}</p>
                  )}
                </div>
              </div>
            )}

            {/* 3단계: 개인정보 */}
            {step === 3 && (
              <div className="space-y-4 animate-slide-in">
                <div className="text-center">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    마지막으로, 이름을 알려주세요
                  </h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    개인화된 학습 경험을 위해 필요합니다
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <UserIcon className="h-5 w-5 text-gray-400" />
                    </div>
                    <input
                      {...register('first_name', { required: '이름을 입력해주세요.' })}
                      type="text"
                      placeholder="이름"
                      className="block w-full pl-10 pr-3 py-3 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-gray-100"
                    />
                  </div>
                  <div className="relative">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                      <UserIcon className="h-5 w-5 text-gray-400" />
                    </div>
                    <input
                      {...register('last_name', { required: '성을 입력해주세요.' })}
                      type="text"
                      placeholder="성"
                      className="block w-full pl-10 pr-3 py-3 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:text-gray-100"
                    />
                  </div>
                </div>
                {(errors.first_name || errors.last_name) && (
                  <div className="text-sm text-red-600 dark:text-red-400">
                    {errors.first_name?.message} {errors.last_name?.message}
                  </div>
                )}
              </div>
            )}

            {/* 네비게이션 버튼 */}
            <div className="flex justify-between space-x-4">
              {step > 1 && (
                <button
                  type="button"
                  onClick={prevStep}
                  className="flex-1 py-3 px-4 border border-gray-300 dark:border-gray-600 rounded-lg shadow-sm bg-white dark:bg-gray-700 text-sm font-medium text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
                >
                  이전
                </button>
              )}
              
              {step < 3 ? (
                <button
                  type="button"
                  onClick={nextStep}
                  disabled={!isStepValid(step)}
                  className="flex-1 py-3 px-4 border border-transparent rounded-lg shadow-sm bg-gradient-to-r from-blue-500 to-purple-600 text-sm font-medium text-white hover:from-blue-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  다음
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={isLoading || !isValid}
                  className="flex-1 py-3 px-4 border border-transparent rounded-lg shadow-sm bg-gradient-to-r from-blue-500 to-purple-600 text-sm font-medium text-white hover:from-blue-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
                >
                  {isLoading ? (
                    <div className="flex items-center justify-center">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                      계정 생성 중...
                    </div>
                  ) : (
                    '🎉 계정 만들기'
                  )}
                </button>
              )}
            </div>
          </form>
        </div>

        {/* 로그인 링크 */}
        <div className="text-center">
          <p className="text-sm text-gray-600 dark:text-gray-400">
            이미 계정이 있으신가요?{' '}
            <Link 
              to="/login" 
              className="font-medium text-blue-600 dark:text-blue-400 hover:text-blue-500 transition-colors"
            >
              로그인하기
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default EnhancedRegisterPage;