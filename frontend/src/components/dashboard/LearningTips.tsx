import React from 'react';

const LearningTips: React.FC = () => {
  const tips = [
    {
      color: 'text-green-500',
      text: '복습은 하루에 조금씩이라도 꾸준히 하는 것이 중요합니다.'
    },
    {
      color: 'text-yellow-500',
      text: '기억이 애매하다면 \'애매함\'으로 표시하여 더 자주 복습하세요.'
    },
    {
      color: 'text-purple-500',
      text: '카테고리와 태그를 활용하여 체계적으로 정리하세요.'
    }
  ];

  return (
    <div className="bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-700 rounded-2xl p-6 shadow-lg dark:shadow-gray-700/20">
      <div className="flex items-center mb-4">
        <div className="text-2xl mr-3">💡</div>
        <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100">학습 팁</h3>
      </div>
      <div className="space-y-3">
        {tips.map((tip, index) => (
          <div key={index} className="flex items-start">
            <div className={`${tip.color} mr-3 mt-1`}>•</div>
            <p className="text-gray-700 dark:text-gray-300">{tip.text}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LearningTips;