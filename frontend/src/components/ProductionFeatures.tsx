import React from 'react';
import { CheckCircleIcon, SparklesIcon, ShieldCheckIcon, ChartBarIcon } from '@heroicons/react/24/outline';

const ProductionFeatures: React.FC = () => {
  const features = [
    {
      icon: SparklesIcon,
      title: '과학적 복습 시스템',
      description: '에빙하우스 망각곡선을 기반으로 한 최적화된 간격 복습 알고리즘',
      color: 'text-purple-600 dark:text-purple-400'
    },
    {
      icon: ChartBarIcon,
      title: '스마트 학습 분석',
      description: '개인화된 학습 패턴 분석과 데이터 기반 성과 향상 제안',
      color: 'text-blue-600 dark:text-blue-400'
    },
    {
      icon: ShieldCheckIcon,
      title: '안전한 데이터 보호',
      description: '엔터프라이즈급 보안으로 학습 데이터를 안전하게 보호',
      color: 'text-green-600 dark:text-green-400'
    },
    {
      icon: CheckCircleIcon,
      title: '오프라인 지원',
      description: 'PWA 기술로 인터넷 연결 없이도 학습 계속 가능',
      color: 'text-orange-600 dark:text-orange-400'
    }
  ];

  return (
    <div className="bg-gradient-to-br from-gray-50 to-blue-50 dark:from-gray-900 dark:to-gray-800 py-16">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-4">
            왜 Resee인가?
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
            과학적 근거와 최신 기술을 바탕으로 한 차세대 학습 플랫폼
          </p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <div 
              key={index}
              className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow-sm border border-gray-200 dark:border-gray-700 hover:shadow-md transition-shadow duration-200"
            >
              <div className="flex flex-col items-center text-center">
                <div className={`w-12 h-12 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center mb-4`}>
                  <feature.icon className={`w-6 h-6 ${feature.color}`} />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default ProductionFeatures;