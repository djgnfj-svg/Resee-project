"""
Base AI service for Claude integration
"""
import time
from typing import Any, Dict, List, Tuple

import anthropic
from django.conf import settings


class AIServiceError(Exception):
    """Custom exception for AI service errors"""
    pass


class BaseAIService:
    """
    Base Claude service for AI operations
    """
    
    def __init__(self):
        """Initialize Claude service with configuration from Django settings"""
        api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)
        try:
            self.client = anthropic.Anthropic(
                api_key=api_key or 'test-key'  # Fallback for testing
            )
        except Exception:
            # Create a mock client for testing when no API key is available
            self.client = type('MockClient', (), {'api_key': api_key})()
        
        # Load configuration from settings with sensible defaults
        self.model = getattr(settings, 'AI_MODEL_NAME', 'claude-3-haiku-20240307')
        self.max_retries = getattr(settings, 'AI_MAX_RETRIES', 3)
        self.cache_timeout = getattr(settings, 'AI_CACHE_TIMEOUT', 3600)  # 1 hour
        self.max_tokens = getattr(settings, 'AI_MAX_TOKENS', 4000)
        self.temperature = getattr(settings, 'AI_TEMPERATURE', 0.7)
    
    def _make_api_call(self, messages: List[Dict], temperature: float = None, max_tokens: int = None) -> Tuple[str, int]:
        """
        Make an API call to Claude with retry logic
        
        Returns:
            Tuple[str, int]: (response_content, processing_time_ms)
        """
        if not hasattr(self.client, 'messages') or not self.client.api_key:
            raise AIServiceError("Claude API key not configured")
        
        temperature = temperature or self.temperature
        max_tokens = max_tokens or self.max_tokens
        start_time = time.time()
        
        # Convert messages to Claude format
        system_message = ""
        user_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            elif msg["role"] == "user":
                user_messages.append(msg["content"])
        
        # Combine user messages if multiple
        user_content = "\n\n".join(user_messages)
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_message,
                    messages=[
                        {"role": "user", "content": user_content}
                    ]
                )
                
                processing_time_ms = int((time.time() - start_time) * 1000)
                return response.content[0].text, processing_time_ms
                
            except anthropic.RateLimitError:
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise AIServiceError("Claude rate limit exceeded")
                
            except anthropic.APIError as e:
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                    continue
                raise AIServiceError(f"Claude API error: {str(e)}")
                
            except Exception as e:
                raise AIServiceError(f"Unexpected error: {str(e)}")
        
        raise AIServiceError("Failed to get response after maximum retries")
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON response from Claude with error handling
        """
        import json
        
        try:
            # Try to extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx == -1 or end_idx == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response_text[start_idx:end_idx]
            return json.loads(json_str)
        
        except (json.JSONDecodeError, ValueError) as e:
            raise AIServiceError(f"Failed to parse AI response as JSON: {str(e)}")
    
    def _validate_response_structure(self, data: Dict, required_fields: List[str]) -> bool:
        """
        Validate that response contains required fields
        """
        for field in required_fields:
            if field not in data:
                raise AIServiceError(f"Missing required field in AI response: {field}")
        return True