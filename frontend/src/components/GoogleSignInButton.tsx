import React, { useEffect, useRef } from 'react';
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
}

const GoogleSignInButton: React.FC<GoogleSignInButtonProps> = ({
  onSuccess,
  onError,
  redirectTo,
}) => {
  const buttonRef = useRef<HTMLDivElement>(null);
  const navigate = useNavigate();
  const { loginWithGoogle } = useAuth();
  
  // Google Client ID가 설정되지 않았으면 컴포넌트를 렌더링하지 않음
  const clientId = process.env.REACT_APP_GOOGLE_CLIENT_ID;

  const initializeGoogleSignIn = React.useCallback(() => {
    if (!window.google || !buttonRef.current) return;

    // Google Sign-In 초기화
    window.google.accounts.id.initialize({
      client_id: clientId,
      callback: handleCredentialResponse,
      auto_select: false,
      cancel_on_tap_outside: true,
    });

    // 버튼 렌더링
    window.google.accounts.id.renderButton(buttonRef.current, {
      theme: 'outline',
      size: 'large',
      width: '100%',
      text: 'signin_with',
      logo_alignment: 'left',
    });
  }, [clientId]);

  useEffect(() => {
    // Google Client ID가 없으면 초기화하지 않음
    if (!clientId) return;
    // Google Sign-In script가 이미 로드되어 있는지 확인
    if (window.google) {
      initializeGoogleSignIn();
    } else {
      // Google Sign-In script 동적 로드
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = initializeGoogleSignIn;
      document.head.appendChild(script);

      return () => {
        document.head.removeChild(script);
      };
    }
  }, [clientId, initializeGoogleSignIn]);


  const handleCredentialResponse = async (response: any) => {
    try {
      const { credential } = response;
      
      if (!credential) {
        throw new Error('Google 인증 정보를 받지 못했습니다.');
      }

      // 백엔드 API 호출
      const result = await loginWithGoogle(credential);
      
      // 커스텀 리다이렉트 경로가 있으면 우선 사용
      if (redirectTo) {
        navigate(redirectTo);
      } else {
        // 신규/기존 사용자 모두 대시보드로
        navigate('/dashboard');
      }
      
      onSuccess?.();
      
    } catch (error: any) {
      console.error('Google 로그인 실패:', error);
      const errorMessage = error.response?.data?.error || error.message || 'Google 로그인에 실패했습니다.';
      onError?.(errorMessage);
    }
  };

  // Google Client ID가 설정되지 않았으면 컴포넌트를 렌더링하지 않음
  if (!clientId) {
    return null;
  }

  return (
    <div className="w-full">
      <div ref={buttonRef} className="w-full flex justify-center"></div>
      <noscript>
        <div className="text-center text-red-600">
          Google 로그인을 사용하려면 JavaScript를 활성화해주세요.
        </div>
      </noscript>
    </div>
  );
};

export default GoogleSignInButton;