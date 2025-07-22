/**
 * Blur Processing Viewer Component
 * Interactive learning through selectively blurred content
 */
import React, { useState, useEffect, useRef } from 'react';
import { toast } from 'react-hot-toast';
import { aiReviewAPI } from '../../utils/ai-review-api';
import type { BlurRegionsResponse, BlurProcessingState } from '../../types/ai-review';
import { Content } from '../../types';

interface BlurProcessingViewerProps {
  content: Content;
  onCompleted?: (revealedCount: number, totalCount: number) => void;
}

export const BlurProcessingViewer: React.FC<BlurProcessingViewerProps> = ({
  content,
  onCompleted
}) => {
  const [state, setState] = useState<BlurProcessingState>({
    blurredText: '',
    blurRegions: [],
    revealedRegions: new Set(),
    concepts: [],
    isLoading: true
  });
  const [showAllAnswers, setShowAllAnswers] = useState(false);
  const [gameMode, setGameMode] = useState(true);
  const textRef = useRef<HTMLDivElement>(null);

  // Generate blur regions
  useEffect(() => {
    const generateBlurRegions = async () => {
      try {
        const response: BlurRegionsResponse = await aiReviewAPI.identifyBlurRegions({
          content_id: content.id
        });

        // Sort regions by importance (highest first) for better learning experience
        const sortedRegions = response.blur_regions.sort((a, b) => b.importance - a.importance);

        setState({
          blurredText: content.content,
          blurRegions: sortedRegions,
          revealedRegions: new Set(),
          concepts: response.concepts,
          isLoading: false
        });

        toast.success(`${sortedRegions.length}개의 핵심 개념이 블러 처리되었습니다! 🎯`);
      } catch (error: any) {
        console.error('Blur regions generation failed:', error);
        toast.error('블러 처리 생성에 실패했습니다');
        setState(prev => ({ ...prev, isLoading: false }));
      }
    };

    generateBlurRegions();
  }, [content.id, content.content]);

  const handleRegionClick = (regionIndex: number) => {
    if (!gameMode) return;

    setState(prev => {
      const newRevealed = new Set(prev.revealedRegions);
      newRevealed.add(regionIndex);
      
      // Provide feedback based on importance
      const region = prev.blurRegions[regionIndex];
      if (region.importance >= 0.9) {
        toast.success('🌟 매우 중요한 개념을 발견했습니다!');
      } else if (region.importance >= 0.8) {
        toast.success('✨ 중요한 개념입니다!');
      } else {
        toast.success('👍 좋습니다!');
      }

      return {
        ...prev,
        revealedRegions: newRevealed
      };
    });
  };

  const revealAll = () => {
    const allIndices = new Set(state.blurRegions.map((_, index) => index));
    setState(prev => ({ ...prev, revealedRegions: allIndices }));
    setShowAllAnswers(true);
    setGameMode(false);
    
    onCompleted?.(allIndices.size, state.blurRegions.length);
  };

  const resetBlurs = () => {
    setState(prev => ({ ...prev, revealedRegions: new Set() }));
    setShowAllAnswers(false);
    setGameMode(true);
  };

  const renderBlurredText = () => {
    if (state.blurRegions.length === 0) {
      return <p className="text-gray-800 leading-relaxed">{state.blurredText}</p>;
    }

    let processedText = state.blurredText;
    const regions = [...state.blurRegions].sort((a, b) => b.start_pos - a.start_pos); // Process from end to beginning

    regions.forEach((region, originalIndex) => {
      const regionIndex = state.blurRegions.indexOf(region);
      const isRevealed = state.revealedRegions.has(regionIndex);
      const { start_pos, end_pos, text, importance, concept_type } = region;

      // Create blur element
      const blurElement = isRevealed ? (
        `<span class="revealed-concept ${getConceptTypeClass(concept_type)}" data-importance="${importance}" title="${concept_type} (중요도: ${Math.round(importance * 100)}%)">${text}</span>`
      ) : (
        `<span class="blurred-concept" data-region-index="${regionIndex}" data-importance="${importance}" title="클릭하여 공개 (${concept_type})">${'█'.repeat(Math.max(2, Math.min(8, text.length)))}</span>`
      );

      // Replace the text
      processedText = processedText.slice(0, start_pos) + blurElement + processedText.slice(end_pos);
    });

    return (
      <div 
        dangerouslySetInnerHTML={{ __html: processedText }}
        onClick={(e) => {
          const target = e.target as HTMLElement;
          if (target.classList.contains('blurred-concept')) {
            const regionIndex = parseInt(target.getAttribute('data-region-index') || '0');
            handleRegionClick(regionIndex);
          }
        }}
        className="text-gray-800 leading-relaxed cursor-pointer select-none"
      />
    );
  };

  const getConceptTypeClass = (conceptType: string) => {
    switch (conceptType.toLowerCase()) {
      case 'definition': return 'bg-blue-200 text-blue-800';
      case 'key_term': return 'bg-green-200 text-green-800';
      case 'process': return 'bg-purple-200 text-purple-800';
      case 'organelle': return 'bg-pink-200 text-pink-800';
      case 'molecule': return 'bg-yellow-200 text-yellow-800';
      case 'function': return 'bg-indigo-200 text-indigo-800';
      case 'property': return 'bg-red-200 text-red-800';
      case 'metaphor': return 'bg-orange-200 text-orange-800';
      default: return 'bg-gray-200 text-gray-800';
    }
  };

  const getProgressPercentage = () => {
    return state.blurRegions.length > 0 
      ? (state.revealedRegions.size / state.blurRegions.length) * 100 
      : 0;
  };

  if (state.isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-purple-600 border-t-transparent mr-3"></div>
          <span className="text-gray-600">AI가 핵심 개념을 분석하고 있습니다...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded font-medium">
            블러 처리 학습
          </span>
          <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
            {state.blurRegions.length}개 핵심 개념
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={gameMode ? revealAll : resetBlurs}
            className={`px-3 py-1 text-xs rounded font-medium ${
              gameMode
                ? 'bg-red-100 text-red-700 hover:bg-red-200'
                : 'bg-blue-100 text-blue-700 hover:bg-blue-200'
            }`}
          >
            {gameMode ? '모든 답안 공개' : '다시 숨기기'}
          </button>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-4">
        <div className="flex items-center justify-between mb-1">
          <span className="text-sm font-medium text-gray-700">학습 진행도</span>
          <span className="text-sm text-gray-600">
            {state.revealedRegions.size} / {state.blurRegions.length} 
            ({Math.round(getProgressPercentage())}%)
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-purple-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${getProgressPercentage()}%` }}
          ></div>
        </div>
      </div>

      {/* Instructions */}
      <div className="mb-4 p-3 bg-purple-50 rounded-lg">
        <p className="text-purple-800 text-sm">
          🎯 <strong>게임 방식:</strong> 블러 처리된 핵심 개념들을 클릭하여 공개해보세요. 
          중요도가 높을수록 더 많은 점수를 얻습니다!
        </p>
      </div>

      {/* Content with Blurred Regions */}
      <div 
        ref={textRef}
        className="mb-6 p-4 bg-gray-50 rounded-lg min-h-40"
      >
        <style>{`
          .blurred-concept {
            background: linear-gradient(45deg, #6b7280, #9ca3af);
            color: transparent;
            border-radius: 4px;
            padding: 2px 4px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: monospace;
          }
          .blurred-concept:hover {
            transform: scale(1.05);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          }
          .revealed-concept {
            border-radius: 4px;
            padding: 2px 4px;
            font-weight: 500;
            transition: all 0.3s ease;
          }
        `}</style>
        {renderBlurredText()}
      </div>

      {/* Stats Panel */}
      {state.revealedRegions.size > 0 && (
        <div className="mb-4 p-4 bg-blue-50 rounded-lg">
          <h4 className="font-medium text-blue-900 mb-2">📊 공개한 개념들</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {Array.from(state.revealedRegions)
              .map(index => state.blurRegions[index])
              .sort((a, b) => b.importance - a.importance)
              .map((region, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-2 bg-white rounded border"
                >
                  <span className="text-sm font-medium">{region.text}</span>
                  <div className="flex items-center gap-2">
                    <span className={`px-2 py-1 text-xs rounded ${getConceptTypeClass(region.concept_type)}`}>
                      {region.concept_type}
                    </span>
                    <span className="text-xs text-gray-600">
                      {Math.round(region.importance * 100)}%
                    </span>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Identified Concepts */}
      {state.concepts.length > 0 && (
        <div className="mt-4">
          <h4 className="font-medium text-gray-900 mb-2 text-sm">🧠 AI가 식별한 주요 개념</h4>
          <div className="flex flex-wrap gap-1">
            {state.concepts.map((concept, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded"
              >
                {concept}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Completion Message */}
      {state.revealedRegions.size === state.blurRegions.length && state.blurRegions.length > 0 && (
        <div className="mt-4 p-4 bg-green-50 rounded-lg border border-green-200">
          <div className="flex items-center gap-2">
            <span className="text-2xl">🎉</span>
            <div>
              <h4 className="font-medium text-green-900">완료!</h4>
              <p className="text-green-700 text-sm">
                모든 핵심 개념을 성공적으로 공개했습니다. 
                학습 내용을 다시 한번 정리해보세요!
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};