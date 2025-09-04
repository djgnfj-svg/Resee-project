import React from 'react';

interface UpgradeModalProps {
  show: boolean;
  onClose: () => void;
  onUpgrade: () => void;
}

const UpgradeModal: React.FC<UpgradeModalProps> = ({
  show,
  onClose,
  onUpgrade,
}) => {
  if (!show) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-gray-800 rounded-2xl p-8 max-w-md w-full mx-4 shadow-2xl">
        <div className="text-center">
          <div className="text-4xl mb-4">🔒</div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            서술형 평가 기능
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            AI 서술형 평가는 <span className="font-semibold text-blue-600 dark:text-blue-400">BASIC 이상 구독</span>에서 사용할 수 있습니다.
          </p>
          
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-4 mb-6">
            <h4 className="font-medium text-blue-900 dark:text-blue-300 mb-2">✨ BASIC 플랜 혜택</h4>
            <ul className="text-sm text-blue-800 dark:text-blue-200 space-y-1 text-left">
              <li>• AI 서술형 평가</li>
              <li>• 주간시험</li>
              <li>• AI 콘텐츠 검사</li>
              <li>• 무제한 복습 기간</li>
            </ul>
          </div>

          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              취소
            </button>
            <button
              onClick={onUpgrade}
              className="flex-1 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all font-semibold"
            >
              업그레이드
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UpgradeModal;