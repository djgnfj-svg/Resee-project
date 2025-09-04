"""
AI Review Services Package

This package contains modularized AI services for the Resee platform:
- BaseAIService: Core AI client functionality
- QuestionGeneratorService: AI question generation
- AnswerEvaluatorService: AI answer evaluation
"""

from .base_ai_service import BaseAIService, AIServiceError
from .question_generator import QuestionGeneratorService
from .answer_evaluator import AnswerEvaluatorService
from .chat_service import AIChatService

# Main service instances
ai_service = BaseAIService()
question_generator = QuestionGeneratorService()
answer_evaluator = AnswerEvaluatorService()
chat_service = AIChatService()

__all__ = [
    'BaseAIService',
    'QuestionGeneratorService', 
    'AnswerEvaluatorService',
    'AIChatService',
    'AIServiceError',
    'ai_service',
    'question_generator',
    'answer_evaluator',
    'chat_service',
]