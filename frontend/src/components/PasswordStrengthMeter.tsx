import React from 'react';
import { 
  CheckCircleIcon, 
  XCircleIcon,
  EyeIcon,
  EyeSlashIcon 
} from '@heroicons/react/24/outline';

interface PasswordStrengthMeterProps {
  password: string;
  showPassword: boolean;
  onToggleVisibility: () => void;
}

interface StrengthCriteria {
  label: string;
  test: (password: string) => boolean;
  icon: 'check' | 'x';
}

const PasswordStrengthMeter: React.FC<PasswordStrengthMeterProps> = ({
  password,
  showPassword,
  onToggleVisibility,
}) => {
  const criteria: StrengthCriteria[] = [
    {
      label: '최소 8자 이상',
      test: (pwd) => pwd.length >= 8,
      icon: 'check',
    },
    {
      label: '영문자 포함',
      test: (pwd) => /[a-zA-Z]/.test(pwd),
      icon: 'check',
    },
    {
      label: '숫자 포함',
      test: (pwd) => /\d/.test(pwd),
      icon: 'check',
    },
    {
      label: '특수문자 포함 (권장)',
      test: (pwd) => /[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>?]/.test(pwd),
      icon: 'check',
    },
  ];

  const getPasswordStrength = () => {
    const passedCriteria = criteria.filter(criterion => criterion.test(password)).length;
    
    if (passedCriteria <= 1) return { level: 'very-weak', label: '매우 약함', color: 'red' };
    if (passedCriteria === 2) return { level: 'weak', label: '약함', color: 'orange' };
    if (passedCriteria === 3) return { level: 'medium', label: '보통', color: 'yellow' };
    return { level: 'strong', label: '강함', color: 'green' };
  };

  const strength = getPasswordStrength();

  // 강도에 따른 색상 클래스
  const getStrengthBarColor = (index: number) => {
    const passedCriteria = criteria.filter(criterion => criterion.test(password)).length;
    
    if (index < passedCriteria) {
      switch (strength.color) {
        case 'red': return 'bg-red-500';
        case 'orange': return 'bg-orange-500';
        case 'yellow': return 'bg-yellow-500';
        case 'green': return 'bg-green-500';
        default: return 'bg-gray-300';
      }
    }
    return 'bg-gray-200 dark:bg-gray-600';
  };

  const getStrengthTextColor = () => {
    switch (strength.color) {
      case 'red': return 'text-red-600 dark:text-red-400';
      case 'orange': return 'text-orange-600 dark:text-orange-400';
      case 'yellow': return 'text-yellow-600 dark:text-yellow-400';
      case 'green': return 'text-green-600 dark:text-green-400';
      default: return 'text-gray-600 dark:text-gray-400';
    }
  };

  if (!password) return null;

  return (
    <div className="mt-3 space-y-3">
      {/* 비밀번호 표시/숨김 토글 */}
      <div className="flex justify-end">
        <button
          type="button"
          onClick={onToggleVisibility}
          className="flex items-center space-x-1 text-sm text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300"
        >
          {showPassword ? (
            <>
              <EyeSlashIcon className="w-4 h-4" />
              <span>숨기기</span>
            </>
          ) : (
            <>
              <EyeIcon className="w-4 h-4" />
              <span>보기</span>
            </>
          )}
        </button>
      </div>

      {/* 강도 표시 바 */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            비밀번호 강도
          </span>
          <span className={`text-sm font-medium ${getStrengthTextColor()}`}>
            {strength.label}
          </span>
        </div>
        
        <div className="flex space-x-1">
          {[0, 1, 2, 3].map((index) => (
            <div
              key={index}
              className={`h-2 flex-1 rounded-full transition-all duration-300 ${getStrengthBarColor(index)}`}
            />
          ))}
        </div>
      </div>

      {/* 기준 체크리스트 */}
      <div className="space-y-2">
        <div className="text-sm font-medium text-gray-700 dark:text-gray-300">
          비밀번호 요구사항
        </div>
        <div className="space-y-1">
          {criteria.map((criterion, index) => {
            const isPassed = criterion.test(password);
            return (
              <div
                key={index}
                className={`flex items-center space-x-2 text-sm transition-colors duration-200 ${
                  isPassed ? 'text-green-600 dark:text-green-400' : 'text-gray-500 dark:text-gray-400'
                }`}
              >
                {isPassed ? (
                  <CheckCircleIcon className="w-4 h-4 text-green-500" />
                ) : (
                  <XCircleIcon className="w-4 h-4 text-gray-400" />
                )}
                <span className={isPassed ? 'line-through' : ''}>{criterion.label}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 추가 팁 */}
      {strength.level === 'very-weak' && (
        <div className="p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="text-sm text-red-700 dark:text-red-300">
            💡 <strong>팁:</strong> 더 안전한 비밀번호를 위해 영문자, 숫자, 특수문자를 조합해보세요.
          </div>
        </div>
      )}

      {strength.level === 'strong' && (
        <div className="p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
          <div className="text-sm text-green-700 dark:text-green-300">
            ✅ <strong>훌륭해요!</strong> 강력한 비밀번호입니다.
          </div>
        </div>
      )}
    </div>
  );
};

export default PasswordStrengthMeter;