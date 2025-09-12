import React, { useState } from 'react';
import { EnvelopeIcon } from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';

interface EmailSignupProps {
  className?: string;
}

const EmailSignup: React.FC<EmailSignupProps> = ({ className = '' }) => {
  const [emailSignup, setEmailSignup] = useState('');
  const [emailSubmitting, setEmailSubmitting] = useState(false);

  const handleEmailSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!emailSignup.trim()) {
      toast.error('이메일을 입력해주세요.');
      return;
    }
    
    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(emailSignup)) {
      toast.error('올바른 이메일 주소를 입력해주세요.');
      return;
    }
    
    setEmailSubmitting(true);
    
    try {
      // Call real API endpoint
      const response = await fetch(`${process.env.REACT_APP_API_URL}/accounts/email-signup/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: emailSignup.trim()
        })
      });
      
      const data = await response.json();
      
      if (response.ok) {
        toast.success(data.message || '구독 관심 신청이 완료되었습니다!');
        setEmailSignup('');
        
        // Store in localStorage to show user feedback
        localStorage.setItem('email_signup_submitted', emailSignup);
      } else {
        toast.error(data.error || '신청 중 오류가 발생했습니다.');
      }
      
    } catch (error) {
      console.error('Email signup error:', error);
      toast.error('신청 중 오류가 발생했습니다. 다시 시도해주세요.');
    } finally {
      setEmailSubmitting(false);
    }
  };

  return (
    <div className={`bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-xl p-8 border border-blue-200 dark:border-blue-700 ${className}`}>
      <div className="text-center mb-6">
        <EnvelopeIcon className="h-12 w-12 text-blue-600 dark:text-blue-400 mx-auto mb-4" />
        <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
          💌 구독 소식 받기
        </h3>
        <p className="text-gray-600 dark:text-gray-400">
          새로운 플랜 출시와 할인 소식을 가장 먼저 받아보세요
        </p>
      </div>

      <form onSubmit={handleEmailSignup} className="space-y-4">
        <div>
          <label htmlFor="email-signup" className="sr-only">
            이메일 주소
          </label>
          <input
            type="email"
            id="email-signup"
            value={emailSignup}
            onChange={(e) => setEmailSignup(e.target.value)}
            placeholder="your-email@example.com"
            className="block w-full rounded-md border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 shadow-sm focus:border-blue-500 focus:ring-blue-500 dark:focus:border-blue-400 dark:focus:ring-blue-400"
            disabled={emailSubmitting}
          />
        </div>
        
        <button
          type="submit"
          disabled={emailSubmitting || !emailSignup.trim()}
          className="w-full bg-gradient-to-r from-blue-600 to-purple-600 text-white py-2 px-4 rounded-md font-medium hover:from-blue-700 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
        >
          {emailSubmitting ? '신청 중...' : '🔔 소식 받기'}
        </button>
      </form>

      <p className="mt-4 text-xs text-gray-500 dark:text-gray-400 text-center">
        스팸 메일은 보내지 않으며, 언제든지 구독 해지할 수 있습니다.
      </p>
    </div>
  );
};

export default EmailSignup;