import React, { useState } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  DocumentTextIcon,
  XMarkIcon,
  ArrowDownTrayIcon,
  MagnifyingGlassIcon,
  LightBulbIcon,
  BookmarkIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';
import { toast } from 'react-hot-toast';
import apiClient from '../utils/apiClient';
import LoadingSpinner from './LoadingSpinner';

interface AISummaryNote {
  id: number;
  content: number;
  summary_type: 'one_page' | 'mind_map' | 'key_points' | 'cornell_notes';
  summary_content: string;
  key_concepts: string[];
  important_terms: Array<{term: string, definition: string}>;
  visual_elements: Record<string, any>;
  study_questions: string[];
  pdf_url: string;
  word_count: number;
  compression_ratio: number;
  ai_model_used: string;
  created_at: string;
}

interface SummaryNoteModalProps {
  isOpen: boolean;
  onClose: () => void;
  contentId: number;
  contentTitle: string;
}

const SummaryNoteModal: React.FC<SummaryNoteModalProps> = ({
  isOpen,
  onClose,
  contentId,
  contentTitle
}) => {
  const queryClient = useQueryClient();
  const [selectedType, setSelectedType] = useState<'one_page' | 'mind_map' | 'key_points' | 'cornell_notes'>('one_page');
  const [userPreferences, setUserPreferences] = useState({
    include_visuals: true,
    include_questions: true,
    language_level: 'intermediate' as 'beginner' | 'intermediate' | 'advanced'
  });

  // 기존 요약 노트 조회
  const { data: existingSummaries } = useQuery({
    queryKey: ['summary-notes', contentId],
    queryFn: async (): Promise<AISummaryNote[]> => {
      const response = await apiClient.get(`/api/ai-review/summary-note/?content_id=${contentId}`);
      return response.data;
    },
    enabled: isOpen
  });

  // 요약 노트 생성
  const generateSummaryMutation = useMutation({
    mutationFn: async () => {
      const response = await apiClient.post('/api/ai-review/summary-note/', {
        content_id: contentId,
        summary_type: selectedType,
        user_preferences: userPreferences
      });
      return response.data;
    },
    onSuccess: (data) => {
      toast.success('요약 노트가 생성되었습니다!');
      queryClient.invalidateQueries({ queryKey: ['summary-notes', contentId] });
    },
    onError: (error: any) => {
      const message = error.response?.data?.detail || '요약 노트 생성에 실패했습니다.';
      toast.error(message);
    }
  });

  const getSummaryTypeLabel = (type: string) => {
    const labels = {
      'one_page': '1페이지 요약',
      'mind_map': '마인드맵',
      'key_points': '핵심 포인트',
      'cornell_notes': '코넬 노트'
    };
    return labels[type as keyof typeof labels] || type;
  };

  const getSummaryTypeDescription = (type: string) => {
    const descriptions = {
      'one_page': '핵심 내용을 A4 한 장으로 압축한 간결한 요약',
      'mind_map': '개념 간 연관성을 시각적으로 표현한 마인드맵',
      'key_points': '중요한 포인트들을 정리한 리스트 형태',
      'cornell_notes': '체계적인 학습을 위한 코넬식 노트'
    };
    return descriptions[type as keyof typeof descriptions] || '';
  };

  const handleDownloadPDF = async (summary: AISummaryNote) => {
    if (summary.pdf_url) {
      const link = document.createElement('a');
      link.href = summary.pdf_url;
      link.download = `${contentTitle}_${getSummaryTypeLabel(summary.summary_type)}.pdf`;
      link.click();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-xl w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* 헤더 */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h3 className="text-xl font-semibold text-gray-900 flex items-center">
                <DocumentTextIcon className="h-6 w-6 text-indigo-600 mr-2" />
                AI 요약 노트
              </h3>
              <p className="text-sm text-gray-600 mt-1">{contentTitle}</p>
            </div>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* 새 요약 노트 생성 */}
          <div className="bg-gray-50 p-6 rounded-lg mb-6">
            <h4 className="text-lg font-medium text-gray-900 mb-4">새 요약 노트 생성</h4>
            
            {/* 요약 유형 선택 */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                요약 형식
              </label>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {(['one_page', 'mind_map', 'key_points', 'cornell_notes'] as const).map((type) => (
                  <label
                    key={type}
                    className={`p-3 border rounded-lg cursor-pointer transition-colors ${
                      selectedType === type
                        ? 'border-indigo-500 bg-indigo-50'
                        : 'border-gray-200 hover:bg-gray-50'
                    }`}
                  >
                    <input
                      type="radio"
                      name="summaryType"
                      value={type}
                      checked={selectedType === type}
                      onChange={(e) => setSelectedType(e.target.value as any)}
                      className="sr-only"
                    />
                    <div>
                      <div className="font-medium text-gray-900">{getSummaryTypeLabel(type)}</div>
                      <div className="text-sm text-gray-600 mt-1">{getSummaryTypeDescription(type)}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            {/* 사용자 설정 */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                추가 옵션
              </label>
              <div className="space-y-2">
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={userPreferences.include_visuals}
                    onChange={(e) => setUserPreferences(prev => ({ ...prev, include_visuals: e.target.checked }))}
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">시각적 요소 포함 (다이어그램, 차트 등)</span>
                </label>
                <label className="flex items-center">
                  <input
                    type="checkbox"
                    checked={userPreferences.include_questions}
                    onChange={(e) => setUserPreferences(prev => ({ ...prev, include_questions: e.target.checked }))}
                    className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="ml-2 text-sm text-gray-700">학습 확인 질문 포함</span>
                </label>
              </div>
            </div>

            {/* 언어 수준 */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                언어 수준
              </label>
              <select
                value={userPreferences.language_level}
                onChange={(e) => setUserPreferences(prev => ({ ...prev, language_level: e.target.value as any }))}
                className="border border-gray-300 rounded px-3 py-2"
              >
                <option value="beginner">초급 (쉬운 언어)</option>
                <option value="intermediate">중급 (표준 언어)</option>
                <option value="advanced">고급 (전문 용어 포함)</option>
              </select>
            </div>

            <button
              onClick={() => generateSummaryMutation.mutate()}
              disabled={generateSummaryMutation.isPending}
              className="w-full bg-indigo-600 text-white py-2 px-4 rounded-lg hover:bg-indigo-700 disabled:opacity-50 transition-colors flex items-center justify-center"
            >
              {generateSummaryMutation.isPending ? (
                <LoadingSpinner className="w-4 h-4 mr-2" />
              ) : (
                <DocumentTextIcon className="w-4 h-4 mr-2" />
              )}
              {generateSummaryMutation.isPending ? '생성 중...' : '요약 노트 생성'}
            </button>
          </div>

          {/* 기존 요약 노트 목록 */}
          {existingSummaries && existingSummaries.length > 0 && (
            <div>
              <h4 className="text-lg font-medium text-gray-900 mb-4">기존 요약 노트</h4>
              <div className="space-y-4">
                {existingSummaries.map((summary) => (
                  <div key={summary.id} className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 transition-colors">
                    <div className="flex items-center justify-between mb-3">
                      <div>
                        <h5 className="font-medium text-gray-900 flex items-center">
                          <DocumentTextIcon className="h-4 w-4 text-indigo-600 mr-1" />
                          {getSummaryTypeLabel(summary.summary_type)}
                        </h5>
                        <p className="text-sm text-gray-600">
                          {new Date(summary.created_at).toLocaleDateString('ko-KR')} • 
                          {summary.word_count}단어 • 압축률 {(summary.compression_ratio * 100).toFixed(1)}%
                        </p>
                      </div>
                      <div className="flex space-x-2">
                        {summary.pdf_url && (
                          <button
                            onClick={() => handleDownloadPDF(summary)}
                            className="p-2 text-gray-600 hover:text-indigo-600 border border-gray-300 rounded hover:bg-white transition-colors"
                          >
                            <ArrowDownTrayIcon className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </div>

                    {/* 요약 내용 미리보기 */}
                    <div className="mb-3">
                      <div className="text-sm text-gray-700 line-clamp-3">
                        {summary.summary_content.substring(0, 200)}...
                      </div>
                    </div>

                    {/* 핵심 개념 */}
                    {summary.key_concepts.length > 0 && (
                      <div className="mb-3">
                        <h6 className="text-sm font-medium text-gray-900 mb-2 flex items-center">
                          <BookmarkIcon className="h-3 w-3 mr-1" />
                          핵심 개념
                        </h6>
                        <div className="flex flex-wrap gap-1">
                          {summary.key_concepts.slice(0, 5).map((concept, index) => (
                            <span
                              key={index}
                              className="inline-block bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded"
                            >
                              {concept}
                            </span>
                          ))}
                          {summary.key_concepts.length > 5 && (
                            <span className="inline-block bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded">
                              +{summary.key_concepts.length - 5}
                            </span>
                          )}
                        </div>
                      </div>
                    )}

                    {/* 중요 용어 */}
                    {summary.important_terms.length > 0 && (
                      <div className="mb-3">
                        <h6 className="text-sm font-medium text-gray-900 mb-2 flex items-center">
                          <MagnifyingGlassIcon className="h-3 w-3 mr-1" />
                          중요 용어
                        </h6>
                        <div className="text-xs text-gray-600">
                          {summary.important_terms.slice(0, 3).map((term, index) => (
                            <span key={index} className="mr-2">
                              <strong>{term.term}</strong>: {term.definition.substring(0, 30)}...
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* 학습 질문 */}
                    {summary.study_questions.length > 0 && (
                      <div>
                        <h6 className="text-sm font-medium text-gray-900 mb-2 flex items-center">
                          <LightBulbIcon className="h-3 w-3 mr-1" />
                          학습 질문 ({summary.study_questions.length}개)
                        </h6>
                        <div className="text-xs text-gray-600">
                          <div>{summary.study_questions[0]}</div>
                          {summary.study_questions.length > 1 && (
                            <div className="text-gray-500">외 {summary.study_questions.length - 1}개</div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 빈 상태 */}
          {(!existingSummaries || existingSummaries.length === 0) && !generateSummaryMutation.isPending && (
            <div className="text-center py-8 text-gray-500">
              <DocumentTextIcon className="mx-auto h-12 w-12 text-gray-400 mb-4" />
              <p>아직 생성된 요약 노트가 없습니다.</p>
              <p className="text-sm">위에서 새로운 요약 노트를 만들어보세요!</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SummaryNoteModal;