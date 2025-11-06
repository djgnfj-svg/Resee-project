import React, { useState, useEffect } from 'react';
import { Content } from '../../types';

interface Category {
  id: number;
  name: string;
  count: number;
}

interface ContentSelectorModalProps {
  show: boolean;
  contents: Content[];
  error: string;
  isLoading: boolean;
  onCreate: (categoryId: number | null) => void;
  onClose: () => void;
}

const ContentSelectorModal: React.FC<ContentSelectorModalProps> = ({
  show,
  contents,
  error,
  isLoading,
  onCreate,
  onClose,
}) => {
  const [selectedCategoryId, setSelectedCategoryId] = useState<number | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);

  useEffect(() => {
    // AI 검증된 콘텐츠만 필터링
    const validatedContents = contents.filter(c => c.is_ai_validated && c.category);

    // 카테고리별로 그룹화
    const categoryMap = new Map<number, { name: string; count: number }>();

    validatedContents.forEach(content => {
      if (content.category) {
        const existing = categoryMap.get(content.category.id);
        if (existing) {
          existing.count += 1;
        } else {
          categoryMap.set(content.category.id, {
            name: content.category.name,
            count: 1
          });
        }
      }
    });

    // Category[] 형태로 변환 (7개 이상인 카테고리만)
    const categoryList: Category[] = Array.from(categoryMap.entries())
      .map(([id, data]) => ({ id, ...data }))
      .filter(cat => cat.count >= 7)
      .sort((a, b) => b.count - a.count);

    setCategories(categoryList);

    // 기본 선택 (첫 번째 카테고리)
    if (categoryList.length > 0) {
      setSelectedCategoryId(categoryList[0].id);
    }
  }, [contents]);

  const selectedCategory = categories.find(c => c.id === selectedCategoryId);
  const isValid = selectedCategoryId !== null;

  if (!show) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-md w-full">
        {/* 헤더 */}
        <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">
          카테고리 선택
        </h3>

        {/* 안내 메시지 */}
        <div className="mb-6 p-4 bg-indigo-50 dark:bg-indigo-900/20 border-l-4 border-indigo-500 rounded-lg">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-indigo-600 dark:text-indigo-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p className="text-indigo-800 dark:text-indigo-200 text-sm leading-relaxed">
                최근 1주일 동안 학습한 카테고리를 선택하면
                해당 카테고리의 <strong>AI 검증 완료 콘텐츠</strong>로 자동으로 시험이 생성됩니다.
              </p>
            </div>
          </div>
        </div>

        {/* 에러 메시지 */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border-l-4 border-red-500 rounded-lg">
            <p className="text-red-800 dark:text-red-200 text-sm font-medium">{error}</p>
          </div>
        )}

        {/* 카테고리 리스트 */}
        {categories.length === 0 ? (
          <div className="mb-6 p-8 text-center border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg">
            <svg className="w-16 h-16 text-gray-400 dark:text-gray-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="text-gray-700 dark:text-gray-300 font-medium mb-1">
              시험 생성 가능한 카테고리가 없습니다
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              카테고리당 AI 검증된 콘텐츠가 최소 7개 이상 필요합니다
            </p>
          </div>
        ) : (
          <div className="mb-6 space-y-2 max-h-96 overflow-y-auto">
            {categories.map((category) => (
              <label
                key={category.id}
                className={`flex items-center justify-between p-4 border-2 rounded-lg cursor-pointer transition-all ${
                  selectedCategoryId === category.id
                    ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20 shadow-md'
                    : 'border-gray-200 dark:border-gray-700 hover:border-indigo-300 dark:hover:border-indigo-600'
                }`}
              >
                <div className="flex items-center flex-1">
                  <input
                    type="radio"
                    name="category"
                    checked={selectedCategoryId === category.id}
                    onChange={() => setSelectedCategoryId(category.id)}
                    className="w-4 h-4 text-indigo-600 focus:ring-indigo-500"
                  />
                  <div className="ml-3 flex-1">
                    <p className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                      {category.name}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                      AI 검증 완료 콘텐츠 {category.count}개
                    </p>
                  </div>
                </div>
                {selectedCategoryId === category.id && (
                  <svg className="w-5 h-5 text-indigo-600 dark:text-indigo-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                )}
              </label>
            ))}
          </div>
        )}

        {/* 선택된 카테고리 정보 */}
        {selectedCategory && (
          <div className="mb-6 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-700 rounded-lg">
            <p className="text-sm text-green-800 dark:text-green-200">
              <strong>{selectedCategory.name}</strong> 카테고리의 콘텐츠로 최대 10개의 문제가 자동 생성됩니다
            </p>
          </div>
        )}

        {/* 버튼 */}
        <div className="flex gap-3">
          <button
            onClick={onClose}
            disabled={isLoading}
            className="flex-1 px-4 py-3 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 font-medium transition-colors disabled:opacity-50"
          >
            취소
          </button>
          <button
            onClick={() => onCreate(selectedCategoryId)}
            disabled={isLoading || !isValid}
            className="flex-1 px-4 py-3 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white rounded-lg font-semibold transition-all duration-200 shadow-md disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed disabled:shadow-none"
          >
            {isLoading ? (
              <span className="flex items-center justify-center gap-2">
                <svg className="animate-spin h-5 w-5" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                생성 중...
              </span>
            ) : '시험 생성'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ContentSelectorModal;
