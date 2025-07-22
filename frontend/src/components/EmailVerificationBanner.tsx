import React, { useState } from 'react';
import { Mail, X, RefreshCw } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { resendVerificationEmail } from '../utils/api';

interface EmailVerificationBannerProps {
  onClose?: () => void;
}

export const EmailVerificationBanner: React.FC<EmailVerificationBannerProps> = ({
  onClose
}) => {
  const { user } = useAuth();
  const [isResending, setIsResending] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);
  const [resendError, setResendError] = useState<string | null>(null);
  const [isDismissed, setIsDismissed] = useState(false);

  if (!user || user.is_email_verified || isDismissed) {
    return null;
  }

  const handleResendEmail = async () => {
    if (!user?.email) return;

    setIsResending(true);
    setResendError(null);

    try {
      await resendVerificationEmail(user.email);
      setResendSuccess(true);
      setTimeout(() => setResendSuccess(false), 3000);
    } catch (error: any) {
      setResendError(error.userMessage || '인증 이메일 발송에 실패했습니다.');
    } finally {
      setIsResending(false);
    }
  };

  const handleDismiss = () => {
    setIsDismissed(true);
    onClose?.();
  };

  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
      <div className="flex items-start gap-3">
        <div className="flex-shrink-0">
          <Mail className="w-5 h-5 text-yellow-600" />
        </div>
        
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-yellow-800">
            이메일 인증이 필요합니다
          </h3>
          <p className="mt-1 text-sm text-yellow-700">
            구독 업그레이드를 위해서는 이메일 주소를 먼저 인증해주세요.
            <strong className="font-medium"> {user.email}</strong>로 인증 이메일을 발송했습니다.
          </p>
          
          <div className="mt-3 flex flex-wrap items-center gap-3">
            <button
              onClick={handleResendEmail}
              disabled={isResending || resendSuccess}
              className="inline-flex items-center gap-2 text-sm font-medium text-yellow-800 hover:text-yellow-900 disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${isResending ? 'animate-spin' : ''}`} />
              {isResending ? '발송 중...' : 
               resendSuccess ? '이메일 발송됨!' : 
               '인증 이메일 재발송'}
            </button>
            
            {resendError && (
              <span className="text-sm text-red-600">{resendError}</span>
            )}
          </div>
        </div>
        
        <button
          onClick={handleDismiss}
          className="flex-shrink-0 p-1 text-yellow-600 hover:text-yellow-800 transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};