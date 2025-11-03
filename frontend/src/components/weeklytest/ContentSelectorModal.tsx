import React, { useState } from 'react';
import { Content } from '../../types';

interface ContentSelectorModalProps {
  show: boolean;
  contents: Content[];
  selectedContentIds: number[];
  error: string;
  isLoading: boolean;
  onToggleContent: (contentId: number) => void;
  onCreate: () => void;
  onClose: () => void;
}

const ContentSelectorModal: React.FC<ContentSelectorModalProps> = ({
  show,
  contents,
  selectedContentIds,
  error,
  isLoading,
  onToggleContent,
  onCreate,
  onClose,
}) => {
  const [searchTerm, setSearchTerm] = useState('');

  if (!show) return null;

  // 검증된 콘텐츠와 미검증 콘텐츠 분리
  const validatedContents = contents.filter(c => c.is_ai_validated);
  const unvalidatedContents = contents.filter(c => !c.is_ai_validated);

  // 검색 필터
  const filteredValidated = validatedContents.filter(c =>
    c.title.toLowerCase().includes(searchTerm.toLowerCase())
  );
  const filteredUnvalidated = unvalidatedContents.filter(c =>
    c.title.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const selectedCount = selectedContentIds.length;
  const isValid = selectedCount >= 7 && selectedCount <= 10;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-xl p-6 max-w-2xl w-full max-h-[90vh] flex flex-col">
        {/* 헤더 */}
        <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
          주간 시험 콘텐츠 선택
        </h3>

        {/* 안내 메시지 */}
        <div className="mb-4 p-4 bg-indigo-50 dark:bg-indigo-900/20 border-2 border-indigo-400 dark:border-indigo-600 rounded-lg">
          <p className="text-indigo-800 dark:text-indigo-200 text-sm">
            <strong>AI 검증이 완료된 콘텐츠</strong>를 <strong>7~10개</strong> 선택해주세요.
            {selectedCount > 0 && (
              <span className={`ml-2 font-semibold ${isValid ? 'text-green-600 dark:text-green-400' : 'text-orange-600 dark:text-orange-400'}`}>
                (현재 {selectedCount}개 선택)
              </span>
            )}
          </p>
        </div>

        {/* 검색 */}
        <div className="mb-4">
          <input
            type="text"
            placeholder="콘텐츠 제목 검색..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>

        {/* 에러 메시지 */}
        {error && (
          <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border-2 border-red-400 dark:border-red-600 rounded-lg">
            <div className="flex items-start">
              <span className="text-red-500 mr-2 text-lg">⚠️</span>
              <p className="text-red-800 dark:text-red-200 text-sm font-medium">{error}</p>
            </div>
          </div>
        )}

        {/* 콘텐츠 리스트 (스크롤 가능) */}
        <div className="flex-1 overflow-y-auto mb-4 border border-gray-200 dark:border-gray-700 rounded-lg">
          {/* AI 검증된 콘텐츠 */}
          {filteredValidated.length > 0 && (
            <div className="p-4">
              <h4 className="text-sm font-semibold text-green-600 dark:text-green-400 mb-3">
                ✓ AI 검증 완료 ({filteredValidated.length}개)
              </h4>
              <div className="space-y-2">
                {filteredValidated.map((content) => (
                  <label
                    key={content.id}
                    className={`flex items-start p-3 border-2 rounded-lg cursor-pointer transition-colors ${
                      selectedContentIds.includes(content.id)
                        ? 'border-indigo-500 bg-indigo-50 dark:bg-indigo-900/20'
                        : 'border-gray-200 dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600'
                    }`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedContentIds.includes(content.id)}
                      onChange={() => onToggleContent(content.id)}
                      className="mt-1 mr-3 w-4 h-4 text-indigo-600 bg-gray-100 border-gray-300 rounded focus:ring-indigo-500"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                          {content.title}
                        </p>
                        {content.ai_validation_score && (
                          <span className="ml-2 text-xs px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full whitespace-nowrap">
                            {content.ai_validation_score.toFixed(0)}점
                          </span>
                        )}
                      </div>
                      {content.category && (
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          {content.category.name}
                        </p>
                      )}
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* AI 미검증 콘텐츠 (선택 불가) */}
          {filteredUnvalidated.length > 0 && (
            <div className="p-4 border-t border-gray-200 dark:border-gray-700">
              <h4 className="text-sm font-semibold text-gray-500 dark:text-gray-400 mb-3">
                ✗ AI 검증 필요 ({filteredUnvalidated.length}개)
              </h4>
              <div className="space-y-2">
                {filteredUnvalidated.map((content) => (
                  <div
                    key={content.id}
                    className="flex items-start p-3 border-2 border-gray-200 dark:border-gray-700 rounded-lg opacity-50"
                  >
                    <input
                      type="checkbox"
                      disabled
                      className="mt-1 mr-3 w-4 h-4 text-gray-400 bg-gray-100 border-gray-300 rounded cursor-not-allowed"
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <p className="text-sm font-medium text-gray-600 dark:text-gray-400 truncate">
                          {content.title}
                        </p>
                        <span className="ml-2 text-xs px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400 rounded-full whitespace-nowrap">
                          검증 필요
                        </span>
                      </div>
                      {content.category && (
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                          {content.category.name}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 콘텐츠 없음 */}
          {filteredValidated.length === 0 && filteredUnvalidated.length === 0 && (
            <div className="p-8 text-center text-gray-500 dark:text-gray-400">
              {searchTerm ? '검색 결과가 없습니다.' : 'AI 검증된 콘텐츠가 없습니다. 먼저 콘텐츠를 생성하고 AI 검증을 완료해주세요.'}
            </div>
          )}
        </div>

        {/* 버튼 */}
        <div className="flex space-x-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
          >
            취소
          </button>
          <button
            onClick={onCreate}
            disabled={isLoading || !isValid}
            className="flex-1 px-4 py-2 bg-gradient-to-r from-indigo-500 to-purple-600 hover:from-indigo-600 hover:to-purple-700 text-white rounded-lg transition-all duration-200 shadow-md disabled:from-gray-400 disabled:to-gray-500 disabled:cursor-not-allowed"
          >
            {isLoading ? '생성 중...' : '시험 생성'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ContentSelectorModal;
