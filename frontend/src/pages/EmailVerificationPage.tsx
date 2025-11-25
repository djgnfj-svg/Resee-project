import React, { useEffect, useState, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { verifyEmail, resendVerificationEmail } from '../utils/api';
import { ApiError } from '../types';

interface VerificationStatus {
  loading: boolean;
  success: boolean;
  error: string;
  message: string;
}

const EmailVerificationPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState<VerificationStatus>({
    loading: true,
    success: false,
    error: '',
    message: '',
  });
  const [resendLoading, setResendLoading] = useState(false);

  const token = searchParams.get('token');
  const email = searchParams.get('email');

  const verifyEmailWithToken = useCallback(async (token: string, email: string) => {
    try {
      setStatus(prev => ({ ...prev, loading: true }));
      const response = await verifyEmail(token, email);
      
      setStatus({
        loading: false,
        success: true,
        error: '',
        message: response.message || '이메일 인증이 완료되었습니다!',
      });

      // Auto redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/login', { 
          state: { 
            message: '이메일 인증이 완료되었습니다. 로그인해주세요.',
            email: email 
          } 
        });
      }, 3000);

    } catch (error) {
      const apiError = error as ApiError;
      setStatus({
        loading: false,
        success: false,
        error: apiError.userMessage || '이메일 인증에 실패했습니다.',
        message: '',
      });
    }
  }, [navigate]);

  useEffect(() => {
    if (token && email) {
      verifyEmailWithToken(token, email);
    } else {
      setStatus({
        loading: false,
        success: false,
        error: '유효하지 않은 인증 링크입니다.',
        message: '',
      });
    }
  }, [token, email, verifyEmailWithToken]);

  const handleResendEmail = async () => {
    if (!email) return;

    try {
      setResendLoading(true);
      const response = await resendVerificationEmail(email);
      setStatus(prev => ({
        ...prev,
        message: response.message || '인증 이메일이 재발송되었습니다.',
        error: '',
      }));
    } catch (error) {
      const apiError = error as ApiError;
      setStatus(prev => ({
        ...prev,
        error: apiError.userMessage || '이메일 재발송에 실패했습니다.',
      }));
    } finally {
      setResendLoading(false);
    }
  };

  const handleGoToLogin = () => {
    navigate('/login', { 
      state: { email: email } 
    });
  };

  const handleGoToHome = () => {
    navigate('/');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-50 via-white to-cyan-50 flex items-center justify-center px-4">
      <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8">
        <div className="text-center">
          <div className="mb-6">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              📧 이메일 인증
            </h1>
          </div>

          {status.loading && (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
              <p className="text-gray-600">이메일을 인증하는 중입니다...</p>
            </div>
          )}

          {status.success && (
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-green-800 mb-2">인증 완료!</h2>
              <p className="text-green-600 mb-4">{status.message}</p>
              <p className="text-sm text-gray-500 mb-4">3초 후 로그인 페이지로 이동합니다...</p>
              
              <div className="space-y-2">
                <button
                  onClick={handleGoToLogin}
                  className="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 transition duration-200"
                >
                  바로 로그인하기
                </button>
                <button
                  onClick={handleGoToHome}
                  className="w-full bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200 transition duration-200"
                >
                  홈으로 가기
                </button>
              </div>
            </div>
          )}

          {status.error && !status.loading && (
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-red-800 mb-2">인증 실패</h2>
              <p className="text-red-600 mb-6">{status.error}</p>
              
              <div className="space-y-3">
                {email && (
                  <button
                    onClick={handleResendEmail}
                    disabled={resendLoading}
                    className="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition duration-200"
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
                )}
                
                <button
                  onClick={handleGoToLogin}
                  className="w-full bg-gray-100 text-gray-700 py-2 px-4 rounded-lg hover:bg-gray-200 transition duration-200"
                >
                  로그인 페이지로 가기
                </button>
                
                <button
                  onClick={handleGoToHome}
                  className="w-full bg-gray-50 text-gray-600 py-2 px-4 rounded-lg hover:bg-gray-100 transition duration-200"
                >
                  홈으로 가기
                </button>
              </div>
            </div>
          )}

          {status.message && !status.error && !status.success && (
            <div className="mt-4 p-3 bg-indigo-50 dark:bg-indigo-900/20 border border-indigo-200 dark:border-indigo-800 rounded-lg">
              <p className="text-indigo-800 dark:text-indigo-200">{status.message}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EmailVerificationPage;