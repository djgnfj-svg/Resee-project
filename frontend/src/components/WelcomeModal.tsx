import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
  XMarkIcon,
  SparklesIcon,
  BookOpenIcon,
  ArrowRightIcon,
} from '@heroicons/react/24/outline';

interface WelcomeModalProps {
  isOpen: boolean;
  onClose: () => void;
  userName?: string;
}

const WelcomeModal: React.FC<WelcomeModalProps> = ({ isOpen, onClose, userName }) => {
  const navigate = useNavigate();

  if (!isOpen) return null;

  const handleStartOnboarding = () => {
    onClose();
    navigate('/content');
  };

  const handleSkipToContent = () => {
    onClose();
    navigate('/content');
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        {/* Background overlay */}
        <div className="fixed inset-0 transition-opacity" aria-hidden="true">
          <div className="absolute inset-0 bg-gray-500 opacity-75 dark:bg-gray-900 dark:opacity-80"></div>
        </div>

        {/* Modal panel */}
        <div className="inline-block align-bottom bg-white dark:bg-gray-800 rounded-2xl px-4 pt-5 pb-4 text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full sm:p-6 animate-bounce-in">
          {/* Close button */}
          <div className="absolute top-4 right-4">
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              <XMarkIcon className="w-6 h-6" />
            </button>
          </div>

          {/* Content */}
          <div className="text-center">
            {/* Icon */}
            <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 mb-4">
              <SparklesIcon className="h-8 w-8 text-white" />
            </div>

            {/* Title */}
            <h3 className="text-2xl leading-6 font-bold text-gray-900 dark:text-gray-100 mb-2">
              🎉 회원가입 완료!
            </h3>
            
            <p className="text-lg text-gray-600 dark:text-gray-400 mb-6">
              {userName ? `${userName}님, ` : ''}Resee에 오신 것을 환영합니다!
            </p>

            {/* Description */}
            <div className="bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/20 dark:to-purple-900/20 rounded-xl p-4 mb-6 border border-blue-200 dark:border-blue-800">
              <div className="flex items-center justify-center mb-2">
                <BookOpenIcon className="w-6 h-6 text-blue-500 mr-2" />
                <span className="font-semibold text-gray-900 dark:text-gray-100">
                  과학적인 학습을 시작해보세요
                </span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                에빙하우스 망각 곡선을 기반으로 한 간격 반복 학습으로 더 효과적으로 기억할 수 있습니다.
              </p>
            </div>

            {/* Action buttons */}
            <div className="space-y-3">
              <button
                onClick={handleStartOnboarding}
                className="w-full flex items-center justify-center px-6 py-3 border border-transparent text-base font-medium rounded-lg text-white bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-all shadow-lg"
              >
                <span>🚀 가이드 보기</span>
                <ArrowRightIcon className="ml-2 w-4 h-4" />
              </button>
              
              <button
                onClick={handleSkipToContent}
                className="w-full px-6 py-3 border border-gray-300 dark:border-gray-600 text-base font-medium rounded-lg text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-700 hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 transition-colors"
              >
                바로 시작하기
              </button>
            </div>

            {/* Small tip */}
            <p className="mt-4 text-xs text-gray-500 dark:text-gray-400">
              💡 언제든지 대시보드에서 가이드를 다시 볼 수 있습니다
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default WelcomeModal;