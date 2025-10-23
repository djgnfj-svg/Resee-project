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
          <div className="text-4xl mb-4"></div>
          <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            주관식 평가 기능
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-6">
            AI 주관식 평가는 <span className="font-semibold text-indigo-600 dark:text-indigo-400">유료 구독</span>에서 사용할 수 있습니다.
          </p>
          
          <div className="bg-indigo-50 dark:bg-indigo-900/20 rounded-lg p-4 mb-6">
            <h4 className="font-medium text-indigo-900 dark:text-indigo-300 mb-2">곧 출시됩니다!</h4>
            <p className="text-sm text-indigo-800 dark:text-indigo-200">
              더 나은 서비스를 위해 유료 구독은 사용자 200명 달성 후 오픈 예정입니다.
              지금 이메일을 등록하시면 오픈 소식을 가장 먼저 받아보실 수 있습니다!
            </p>
          </div>

          <div className="flex space-x-3">
            <button
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
            >
              확인
            </button>
            <button
              onClick={onUpgrade}
              className="flex-1 px-4 py-2 bg-indigo-500 text-white rounded-lg hover:bg-indigo-600 transition-all font-semibold"
            >
              이메일 등록하기
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UpgradeModal;