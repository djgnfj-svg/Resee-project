/**
 * AI Question Generator Component
 * Allows users to generate AI-powered questions from their content
 */
import React, { useState, useEffect } from 'react';
import { toast } from 'react-hot-toast';
import { aiReviewAPI } from '../../utils/ai-review-api';
import type { 
  AIQuestionType, 
  AIQuestion, 
  GenerateQuestionsRequest,
  QuestionGenerationState 
} from '../../types/ai-review';
import { Content } from '../../types';

interface AIQuestionGeneratorProps {
  content: Content;
  onQuestionsGenerated?: (questions: AIQuestion[]) => void;
}

export const AIQuestionGenerator: React.FC<AIQuestionGeneratorProps> = ({
  content,
  onQuestionsGenerated
}) => {
  const [questionTypes, setQuestionTypes] = useState<AIQuestionType[]>([]);
  const [state, setState] = useState<QuestionGenerationState>({
    isLoading: false,
    selectedTypes: ['multiple_choice'],
    difficulty: 3,
    count: 3,
    questions: []
  });

  // Load available question types
  useEffect(() => {
    const loadQuestionTypes = async () => {
      try {
        const types = await aiReviewAPI.getQuestionTypes();
        setQuestionTypes(types);
      } catch (error) {
        console.error('Failed to load question types:', error);
        toast.error('Failed to load question types');
      }
    };

    loadQuestionTypes();
  }, []);

  const handleGenerateQuestions = async () => {
    if (state.selectedTypes.length === 0) {
      toast.error('Please select at least one question type');
      return;
    }

    setState(prev => ({ ...prev, isLoading: true, error: undefined }));

    try {
      const request: GenerateQuestionsRequest = {
        content_id: content.id,
        question_types: state.selectedTypes,
        difficulty: state.difficulty,
        count: state.count
      };

      const questions = await aiReviewAPI.generateQuestions(request);
      
      setState(prev => ({ ...prev, questions }));
      onQuestionsGenerated?.(questions);
      
      toast.success(`${questions.length} AI questions generated successfully! 🤖`);
    } catch (error: any) {
      console.error('Question generation failed:', error);
      const errorMessage = error.response?.data?.error || 'Question generation failed';
      setState(prev => ({ ...prev, error: errorMessage }));
      toast.error(errorMessage);
    } finally {
      setState(prev => ({ ...prev, isLoading: false }));
    }
  };

  const handleTypeToggle = (typeName: string) => {
    setState(prev => ({
      ...prev,
      selectedTypes: prev.selectedTypes.includes(typeName)
        ? prev.selectedTypes.filter(t => t !== typeName)
        : [...prev.selectedTypes, typeName]
    }));
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-6 mb-6">
      <div className="flex items-center gap-2 mb-4">
        <div className="p-2 bg-purple-100 rounded-lg">
          🤖
        </div>
        <h3 className="text-lg font-semibold text-gray-900">
          AI Question Generator
        </h3>
        <span className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded-full font-medium">
          AI Feature
        </span>
      </div>

      <p className="text-gray-600 text-sm mb-4">
        AI automatically generates various types of questions from the "{content.title}" content.
      </p>

      {/* Question Type Selection */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Select Question Types
        </label>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
          {questionTypes.map((type) => (
            <label
              key={type.name}
              className={`flex items-center p-3 border rounded-lg cursor-pointer transition-all ${
                state.selectedTypes.includes(type.name)
                  ? 'border-purple-500 bg-purple-50'
                  : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              <input
                type="checkbox"
                checked={state.selectedTypes.includes(type.name)}
                onChange={() => handleTypeToggle(type.name)}
                className="sr-only"
              />
              <div className="flex-1">
                <div className="font-medium text-sm">
                  {aiReviewAPI.getQuestionTypeLabel(type.name)}
                </div>
                <div className="text-xs text-gray-500">
                  {type.description}
                </div>
              </div>
            </label>
          ))}
        </div>
      </div>

      {/* Difficulty and Count Settings */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Difficulty Level
          </label>
          <select
            value={state.difficulty}
            onChange={(e) => setState(prev => ({ ...prev, difficulty: Number(e.target.value) }))}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            <option value={1}>1 - Very Easy</option>
            <option value={2}>2 - Easy</option>
            <option value={3}>3 - Medium</option>
            <option value={4}>4 - Hard</option>
            <option value={5}>5 - Very Hard</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Number of Questions
          </label>
          <select
            value={state.count}
            onChange={(e) => setState(prev => ({ ...prev, count: Number(e.target.value) }))}
            className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          >
            <option value={1}>1</option>
            <option value={2}>2</option>
            <option value={3}>3</option>
            <option value={5}>5</option>
            <option value={7}>7</option>
            <option value={10}>10</option>
          </select>
        </div>
      </div>

      {/* Error Message */}
      {state.error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-700 text-sm">{state.error}</p>
        </div>
      )}

      {/* Generate Button */}
      <button
        onClick={handleGenerateQuestions}
        disabled={state.isLoading || state.selectedTypes.length === 0}
        className={`w-full py-2 px-4 rounded-md font-medium transition-all ${
          state.isLoading || state.selectedTypes.length === 0
            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
            : 'bg-purple-600 text-white hover:bg-purple-700'
        }`}
      >
        {state.isLoading ? (
          <div className="flex items-center justify-center gap-2">
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-white border-t-transparent"></div>
            AI is generating questions...
          </div>
        ) : (
          `🧠 Generate ${state.count} AI Questions`
        )}
      </button>

      {/* Generated Questions Preview */}
      {state.questions.length > 0 && (
        <div className="mt-6">
          <h4 className="font-medium text-gray-900 mb-3">
            Generated Questions Preview ({state.questions.length})
          </h4>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {state.questions.map((question, index) => (
              <div
                key={question.id}
                className="p-3 bg-gray-50 rounded-lg border"
              >
                <div className="flex items-start gap-2">
                  <span className="flex-shrink-0 w-6 h-6 bg-purple-100 text-purple-700 rounded-full flex items-center justify-center text-xs font-medium">
                    {index + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded font-medium">
                        {aiReviewAPI.getQuestionTypeLabel(question.question_type_display.toLowerCase().replace(' ', '_'))}
                      </span>
                      <span className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded">
                        {aiReviewAPI.getDifficultyLabel(question.difficulty)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-900 truncate" title={question.question_text}>
                      {question.question_text}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};