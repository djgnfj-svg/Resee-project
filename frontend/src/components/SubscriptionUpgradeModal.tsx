import React, { useEffect } from 'react';
import { X } from 'lucide-react';
import { useSubscription } from '../hooks/useSubscription';

interface SubscriptionUpgradeModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SubscriptionUpgradeModal: React.FC<SubscriptionUpgradeModalProps> = ({
  isOpen,
  onClose,
}) => {
  const {
    upgradeSuccess,
  } = useSubscription();

  // Close modal on successful upgrade
  useEffect(() => {
    if (upgradeSuccess) {
      const timer = setTimeout(() => {
        onClose();
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [upgradeSuccess, onClose]);

  if (!isOpen) return null;



  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        <div className="fixed inset-0 bg-black bg-opacity-50" onClick={onClose} />
        
        <div className="relative bg-white rounded-xl shadow-xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
          <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900">유료 구독 안내</h2>
            <button
              onClick={onClose}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          <div className="p-6">
            {/* Coming Soon Message */}
            <div className="text-center py-12">
              <h3 className="text-3xl font-bold text-gray-900 mb-4">
                곧 출시됩니다!
              </h3>
              <p className="text-lg text-gray-600 mb-8 max-w-2xl mx-auto">
                더 나은 서비스를 위해 유료 구독은 사용자 200명 달성 후 오픈 예정입니다.
                지금 이메일을 등록하시면 오픈 소식을 가장 먼저 받아보실 수 있습니다!
              </p>
              
              <div className="max-w-md mx-auto mb-8">
                <div className="bg-indigo-50 rounded-lg p-6 border-2 border-indigo-200">
                  <h4 className="font-bold text-indigo-900 mb-3">오픈 알림 신청</h4>
                  <p className="text-sm text-indigo-700 mb-4">
                    유료 구독 오픈 시 가장 먼저 알려드립니다
                  </p>
                  <button
                    onClick={onClose}
                    className="w-full bg-indigo-500 text-white py-3 px-6 rounded-lg hover:bg-indigo-600 transition-all font-semibold"
                  >
                    이메일 등록하러 가기
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};