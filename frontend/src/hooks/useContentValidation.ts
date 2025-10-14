import { useState, useCallback } from 'react';
import { contentAPI } from '../utils/api';

export interface ValidationResult {
  is_valid: boolean;
  factual_accuracy: { score: number; issues: string[] };
  logical_consistency: { score: number; issues: string[] };
  title_relevance: { score: number; issues: string[] };
  overall_feedback: string;
}

export const useContentValidation = () => {
  const [isValidating, setIsValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<ValidationResult | null>(null);

  const validateContent = useCallback(async (title: string, content: string) => {
    if (!title?.trim() || !content?.trim()) return;

    setIsValidating(true);
    setValidationResult(null);

    try {
      const result = await contentAPI.validateContent(title, content);
      setValidationResult(result);
    } catch (error: any) {
      alert(`AI 검증 실패: ${error.response?.data?.error || error.message}`);
    } finally {
      setIsValidating(false);
    }
  }, []);

  const clearValidation = useCallback(() => {
    setValidationResult(null);
  }, []);

  return {
    isValidating,
    validationResult,
    validateContent,
    clearValidation,
  };
};
