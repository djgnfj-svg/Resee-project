"""
AI Chat Service for content-based conversations
"""
import logging
from typing import Dict

from .base_ai_service import BaseAIService, AIServiceError
from ..mock_responses import AIMockResponses

logger = logging.getLogger(__name__)


class AIChatService(BaseAIService):
    """
    Service for AI-powered chat about learning content
    """
    
    def chat_about_content(self, content_text: str, content_title: str, 
                          user_message: str) -> Dict:
        """
        Generate AI chat response about content
        
        Args:
            content_text: The content text to chat about
            content_title: The content title
            user_message: User's message/question
            
        Returns:
            Dictionary with chat response
        """
        # Use mock responses if enabled
        if self.use_mock_responses:
            logger.info("Using mock responses for AI chat")
            mock_response = AIMockResponses.get_chat_response(
                content_text=content_text,
                content_title=content_title,
                user_message=user_message
            )
            return mock_response
        
        # Real AI implementation
        prompt = self._build_chat_prompt(content_text, content_title, user_message)
        
        messages = [
            {"role": "system", "content": self._get_chat_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        try:
            response_text, processing_time = self._make_api_call(messages)
            chat_data = self._parse_json_response(response_text)
            
            return {
                'response': chat_data.get('response', response_text),
                'helpful': chat_data.get('helpful', True),
                'confidence_score': chat_data.get('confidence_score', 0.8),
                'processing_time_ms': processing_time,
                'follow_up_suggestions': chat_data.get('follow_up_suggestions', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to generate chat response: {str(e)}")
            raise AIServiceError(f"Chat generation failed: {str(e)}")
    
    def _build_chat_prompt(self, content_text: str, content_title: str, 
                          user_message: str) -> str:
        """
        Build prompt for chat response
        """
        return f"""
다음 학습 콘텐츠에 대한 사용자의 질문에 도움이 되는 답변을 제공해주세요.

**학습 콘텐츠:**
제목: {content_title}
내용: {content_text}

**사용자 질문:**
{user_message}

**답변 요구사항:**
- 콘텐츠와 관련된 도움이 되는 답변을 제공하세요
- 학습에 도움이 되도록 설명해주세요
- 필요시 추가 질문을 제안해주세요
- 친근하고 교육적인 톤을 사용하세요

**응답 형식 (JSON):**
{{
  "response": "답변 내용",
  "helpful": true,
  "confidence_score": 0.9,
  "follow_up_suggestions": ["추가 질문 1", "추가 질문 2"]
}}
"""
    
    def _get_chat_system_prompt(self) -> str:
        """
        Get system prompt for chat
        """
        return """
당신은 학습 도우미 AI입니다. 학습자가 제공한 콘텐츠에 대해 질문하면, 
이해하기 쉽고 도움이 되는 답변을 제공합니다.

**답변 원칙:**
1. 콘텐츠 기반으로만 답변하세요
2. 정확하고 명확한 설명을 제공하세요
3. 학습자의 이해를 돕는 방향으로 답변하세요
4. 추가 학습을 위한 질문을 제안하세요
5. 친근하고 격려하는 톤을 유지하세요

반드시 지정된 JSON 형식으로 응답하세요.
"""