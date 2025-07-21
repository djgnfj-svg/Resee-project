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
      console.error('Resend verification failed:', error);
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
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-cyan-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8">
        <div className="text-center">
          <div className="mb-6">
            <div className="w-16 h-16 bg-indigo-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 7.89a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-gray-900 mb-2">
              이메일을 확인해주세요
            </h1>
            <p className="text-gray-600">
              회원가입이 완료되었습니다!
            </p>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <div className="flex items-center mb-3">
              <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <p className="text-sm font-medium text-blue-800">
                다음 단계
              </p>
            </div>
            <div className="text-left text-sm text-blue-700 space-y-2">
              <div className="flex items-start">
                <span className="inline-block w-2 h-2 bg-blue-600 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                <span><strong>{email}</strong>로 발송된 인증 이메일을 확인하세요</span>
              </div>
              <div className="flex items-start">
                <span className="inline-block w-2 h-2 bg-blue-600 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                <span>이메일에서 "이메일 인증하기" 버튼을 클릭하세요</span>
              </div>
              <div className="flex items-start">
                <span className="inline-block w-2 h-2 bg-blue-600 rounded-full mr-2 mt-2 flex-shrink-0"></span>
                <span>인증 완료 후 로그인하여 학습을 시작하세요</span>
              </div>
            </div>
          </div>

          {resendMessage && (
            <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-green-800 text-sm">{resendMessage}</p>
            </div>
          )}

          {resendError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-800 text-sm">{resendError}</p>
            </div>
          )}

          <div className="space-y-3">
            <button
              onClick={handleResendEmail}
              disabled={resendLoading || !email}
              className="w-full bg-indigo-600 text-white py-2.5 px-4 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition duration-200 font-medium"
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

            <div className="text-sm text-gray-500">
              이메일이 보이지 않나요? 스팸 폴더를 확인해보세요.
            </div>

            <div className="border-t border-gray-200 pt-4 mt-6 space-y-2">
              <button
                onClick={handleGoToLogin}
                className="w-full bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200 transition duration-200"
              >
                로그인 페이지로 가기
              </button>
              
              <button
                onClick={handleGoToHome}
                className="w-full text-gray-500 hover:text-gray-700 transition duration-200"
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