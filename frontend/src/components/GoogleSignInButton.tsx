import React, { useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

declare global {
  interface Window {
    google: any;
  }
}

interface GoogleSignInButtonProps {
  onSuccess?: () => void;
  onError?: (error: string) => void;
  redirectTo?: string;  // 로그인 후 이동할 경로
  buttonText?: string;  // 버튼 텍스트 (로그인/회원가입)
  disabled?: boolean;   // 버튼 비활성화 여부
}

const GoogleSignInButton: React.FC<GoogleSignInButtonProps> = ({
  onSuccess,
  onError,
  redirectTo,
  buttonText = "Google로 로그인",
  disabled = false,
}) => {
  const navigate = useNavigate();
  const { loginWithGoogle } = useAuth();
  
  // Google Client ID가 설정되지 않았으면 컴포넌트를 렌더링하지 않음
  const clientId = process.env.REACT_APP_GOOGLE_CLIENT_ID;

  const handleCredentialResponse = useCallback(async (response: any) => {
    try {
      const { credential } = response;

      if (!credential) {
        throw new Error('Google 인증 정보를 받지 못했습니다.');
      }

      // 백엔드 API 호출
      await loginWithGoogle(credential);

      // 커스텀 리다이렉트 경로가 있으면 우선 사용
      if (redirectTo) {
        navigate(redirectTo);
      } else {
        // 신규/기존 사용자 모두 대시보드로
        navigate('/dashboard');
      }

      onSuccess?.();

    } catch (error: any) {
      const errorMessage = error.response?.data?.error || error.message || 'Google 로그인에 실패했습니다.';
      onError?.(errorMessage);
    }
  }, [loginWithGoogle, navigate, redirectTo, onSuccess, onError]);

  const handleGoogleSignIn = async () => {
    if (disabled || !window.google) return;

    try {
      // Google One Tap 프롬프트 표시
      window.google.accounts.id.initialize({
        client_id: clientId,
        callback: handleCredentialResponse,
      });
      window.google.accounts.id.prompt();
    } catch (error) {
      onError?.('Google 로그인 초기화에 실패했습니다.');
    }
  };

  useEffect(() => {
    // Google Client ID가 없으면 초기화하지 않음
    if (!clientId) return;

    // Google Sign-In script 동적 로드
    if (!window.google) {
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      document.head.appendChild(script);

      return () => {
        if (document.head.contains(script)) {
          document.head.removeChild(script);
        }
      };
    }
  }, [clientId]);

  // Google Client ID가 설정되지 않았으면 준비 중 버튼 표시
  if (!clientId) {
    return (
      <div className="w-full">
        <button
          type="button"
          disabled
          className="w-full flex items-center justify-center gap-3 px-4 py-2.5 border border-gray-300 rounded shadow-sm bg-white text-sm font-medium text-gray-700 cursor-not-allowed opacity-60"
          style={{ height: '40px' }}
        >
          <svg className="w-[18px] h-[18px]" viewBox="0 0 24 24">
            <path fill="#4285f4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34a853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#fbbc05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#ea4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          <span className="flex-1 text-left">
            {buttonText} (준비 중)
          </span>
        </button>
      </div>
    );
  }

  const isDisabledForTerms = disabled;

  return (
    <div className="w-full">
      <button
        type="button"
        onClick={handleGoogleSignIn}
        disabled={disabled}
        className={`w-full flex items-center justify-center gap-3 px-4 py-2.5 border border-gray-300 rounded shadow-sm bg-white text-sm font-medium text-gray-700 transition-opacity ${
          disabled ? 'cursor-not-allowed opacity-60' : 'hover:bg-gray-50 cursor-pointer'
        }`}
        style={{ height: '40px' }}
      >
        <svg className="w-[18px] h-[18px]" viewBox="0 0 24 24">
          <path fill="#4285f4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
          <path fill="#34a853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
          <path fill="#fbbc05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
          <path fill="#ea4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
        </svg>
        <span className="flex-1 text-left">
          {buttonText}
        </span>
      </button>
      {isDisabledForTerms && (
        <p className="mt-2 text-xs text-gray-500 dark:text-gray-400 text-center">
          약관에 동의한 후 이용하실 수 있습니다.
        </p>
      )}
    </div>
  );
};

export default GoogleSignInButton;