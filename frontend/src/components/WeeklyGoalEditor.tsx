import React, { useState } from 'react';
import { PencilIcon, CheckIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface WeeklyGoalEditorProps {
  currentGoal: number;
  onSave?: (newGoal: number) => Promise<void>;
  onGoalUpdate?: (newGoal: number) => Promise<void>;
  disabled?: boolean;
}

const WeeklyGoalEditor: React.FC<WeeklyGoalEditorProps> = ({ 
  currentGoal, 
  onGoalUpdate,
  onSave,
  disabled = false 
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [goalValue, setGoalValue] = useState(currentGoal.toString());
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleEdit = () => {
    setIsEditing(true);
    setGoalValue(currentGoal.toString());
    setError(null);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setGoalValue(currentGoal.toString());
    setError(null);
  };

  const handleSave = async () => {
    const newGoal = parseInt(goalValue);
    
    // 클라이언트 사이드 검증
    if (isNaN(newGoal) || newGoal < 1 || newGoal > 1000) {
      setError('주간 목표는 1회 이상 1000회 이하로 설정해주세요.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const updateFunction = onSave || onGoalUpdate;
      if (updateFunction) {
        await updateFunction(newGoal);
        setIsEditing(false);
      }
    } catch (err: any) {
      setError(err.message || '목표 설정 중 오류가 발생했습니다.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSave();
    } else if (e.key === 'Escape') {
      handleCancel();
    }
  };

  if (!isEditing) {
    return (
      <div className="flex items-center space-x-2">
        <span className="text-2xl font-bold text-gray-900 dark:text-white">
          {currentGoal}회
        </span>
        {!disabled && (
          <button 
            onClick={handleEdit}
            className="p-1 text-gray-400 hover:text-blue-600 dark:hover:text-blue-400 transition-colors"
            title="목표 수정"
          >
            <PencilIcon className="w-4 h-4" />
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="flex flex-col space-y-2">
      <div className="flex items-center space-x-2">
        <input
          type="number"
          value={goalValue}
          onChange={(e) => setGoalValue(e.target.value)}
          onKeyDown={handleKeyDown}
          min="1"
          max="1000"
          className="w-20 px-2 py-1 text-lg font-bold text-center border border-gray-300 dark:border-gray-600 rounded bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-blue-500"
          autoFocus
          disabled={isLoading}
        />
        <span className="text-lg font-medium text-gray-700 dark:text-gray-300">회</span>
        
        <div className="flex items-center space-x-1">
          <button
            onClick={handleSave}
            disabled={isLoading}
            className="p-1 text-green-600 hover:text-green-700 dark:text-green-400 dark:hover:text-green-300 disabled:opacity-50 transition-colors"
            title="저장"
          >
            <CheckIcon className="w-4 h-4" />
          </button>
          <button
            onClick={handleCancel}
            disabled={isLoading}
            className="p-1 text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300 disabled:opacity-50 transition-colors"
            title="취소"
          >
            <XMarkIcon className="w-4 h-4" />
          </button>
        </div>
      </div>
      
      {error && (
        <div className="text-sm text-red-600 dark:text-red-400">
          {error}
        </div>
      )}
      
      {isLoading && (
        <div className="text-sm text-gray-500 dark:text-gray-400">
          저장 중...
        </div>
      )}
    </div>
  );
};

export default WeeklyGoalEditor;