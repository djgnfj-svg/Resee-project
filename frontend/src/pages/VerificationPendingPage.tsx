import React, { useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { resendVerificationEmail } from '../utils/api';

const VerificationPendingPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [resendLoading, setResendLoading] = useState(false);
  const [resendMessage, setResendMessage] = useState('');
  const [resendError, setResendError] = useState('');

  const email = searchParams.get('email') || '';

  const handleResendEmail = async () => {
    if (!email) return;

    try {
      setResendLoading(true);
      setResendError('');
      const response = await resendVerificationEmail(email);
      setResendMessage(response.message || '인증 이메일이 재발송되었습니다.');
    } catch (error: any) {
      setResendError(error.userMessage || '이메일 재발송에 실패했습니다.');
    } finally {
      setResendLoading(false);
    }
  };

  const handleGoToLogin = () => {
    navigate('/login', { state: { email } });
  };

  const handleGoToHome = () => {
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-cyan-50 dark:from-gray-900 dark:via-gray-800 dark:to-gray-900 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white dark:bg-gray-800 rounded-xl shadow-lg p-8">
        <div className="text-center">
          <div className="mb-6">
            <div className="w-16 h-16 bg-indigo-100 dark:bg-indigo-900 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 7.89a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              이메일을 확인해주세요
            </h1>
            <p className="text-gray-600 dark:text-gray-300">
              회원가입이 완료되었습니다!
            </p>
          </div>

          <div className="bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg p-4 mb-6">
            <div className="flex items-center mb-3">
              <div className="w-8 h-8 bg-indigo-100 dark:bg-indigo-900 rounded-full flex items-center justify-center mr-3">
                <svg className="w-4 h-4 text-indigo-600 dark:text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-sm font-medium text-indigo-800 dark:text-indigo-200">
                다음 단계
              </p>
            </div>
            <div className="text-left text-sm text-indigo-700 dark:text-indigo-300 space-y-2">
              <div className="flex items-start">
                <span className="inline-block w-2 h-2 bg-indigo-600 dark:bg-indigo-400 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                <span><strong>{email}</strong>로 발송된 인증 이메일을 확인하세요</span>
              </div>
              <div className="flex items-start">
                <span className="inline-block w-2 h-2 bg-indigo-600 dark:bg-indigo-400 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                <span>이메일에서 "이메일 인증하기" 버튼을 클릭하세요</span>
              </div>
              <div className="flex items-start">
                <span className="inline-block w-2 h-2 bg-indigo-600 dark:bg-indigo-400 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                <span>인증 완료 후 로그인하여 학습을 시작하세요</span>
              </div>
            </div>
          </div>

          {resendMessage && (
            <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
              <p className="text-green-800 dark:text-green-200 text-sm">{resendMessage}</p>
            </div>
          )}

          {resendError && (
            <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-red-800 dark:text-red-200 text-sm">{resendError}</p>
            </div>
          )}

          <div className="space-y-3">
            <button
              onClick={handleResendEmail}
              disabled={resendLoading || !email}
              className="w-full bg-indigo-600 dark:bg-indigo-500 text-white py-2.5 px-4 rounded-lg hover:bg-indigo-700 dark:hover:bg-indigo-600 disabled:opacity-50 disabled:cursor-not-allowed transition duration-200 font-medium"
            >
              {resendLoading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  발송 중...
                </div>
              ) : (
                '인증 이메일 재발송'
              )}
            </button>

            <div className="text-sm text-gray-500 dark:text-gray-400">
              이메일이 보이지 않나요? 스팸 폴더를 확인해보세요.
            </div>

            <div className="border-t border-gray-200 dark:border-gray-700 pt-4 mt-6 space-y-2">
              <button
                onClick={handleGoToLogin}
                className="w-full bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-200 py-2 px-4 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition duration-200"
              >
                로그인 페이지로 가기
              </button>

              <button
                onClick={handleGoToHome}
                className="w-full text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition duration-200"
              >
                홈으로 가기
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default VerificationPendingPage;