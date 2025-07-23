"""
AI service integration for question generation and answer evaluation
"""
import openai
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from django.conf import settings
from django.core.cache import cache
from .models import AIQuestion, AIEvaluation, AIQuestionType
from content.models import Content


class AIServiceError(Exception):
    """Custom exception for AI service errors"""
    pass


class OpenAIService:
    """
    OpenAI service for question generation and answer evaluation
    """
    
    def __init__(self):
        """Initialize OpenAI service with configuration from Django settings"""
        api_key = getattr(settings, 'OPENAI_API_KEY', None)
        try:
            self.client = openai.OpenAI(
                api_key=api_key or 'test-key'  # Fallback for testing
            )
        except Exception:
            # Create a mock client for testing when no API key is available
            self.client = type('MockClient', (), {'api_key': api_key})()
        
        # Load configuration from settings with sensible defaults
        self.model = getattr(settings, 'OPENAI_MODEL', 'gpt-4')
        self.max_retries = getattr(settings, 'AI_MAX_RETRIES', 3)
        self.cache_timeout = getattr(settings, 'AI_CACHE_TIMEOUT', 3600)  # 1 hour
    
    def _make_api_call(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 1000) -> Tuple[str, int]:
        """
        Make an API call to OpenAI with retry logic
        
        Returns:
            Tuple[str, int]: (response_content, processing_time_ms)
        """
        if not self.client.api_key:
            raise AIServiceError("OpenAI API key not configured")
        
        start_time = time.time()
        
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                
                processing_time_ms = int((time.time() - start_time) * 1000)
                return response.choices[0].message.content, processing_time_ms
                
            except openai.RateLimitError:
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                raise AIServiceError("OpenAI rate limit exceeded")
                
            except openai.APIError as e:
                if attempt < self.max_retries - 1:
                    time.sleep(1)
                    continue
                raise AIServiceError(f"OpenAI API error: {str(e)}")
                
            except Exception as e:
                raise AIServiceError(f"Unexpected error: {str(e)}")
        
        raise AIServiceError("Failed to get response after maximum retries")
    
    def generate_questions(self, content: Content, question_types: List[str], difficulty: int = 1, count: int = 3) -> List[Dict]:
        """
        Generate questions for given content
        
        Args:
            content: Content object to generate questions for
            question_types: List of question type names
            difficulty: Difficulty level (1-5)
            count: Number of questions to generate
        
        Returns:
            List of question dictionaries
        """
        # Check cache first to avoid redundant API calls
        cache_key = f"ai_questions_{content.id}_{'-'.join(question_types)}_{difficulty}_{count}"
        cached_questions = cache.get(cache_key)
        if cached_questions:
            return cached_questions
        
        # Prepare content for AI processing (limit to prevent token overflow)
        content_text = content.content[:2000]  # Limit content length for API efficiency
        
        system_message = """You are an educational AI that generates high-quality review questions. 
        Create questions that test understanding and help with spaced repetition learning.
        
        Return your response as valid JSON with this structure:
        {
            "questions": [
                {
                    "question_type": "multiple_choice",
                    "question_text": "Question text here?",
                    "correct_answer": "Correct answer",
                    "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
                    "explanation": "Why this is correct",
                    "keywords": ["keyword1", "keyword2"]
                }
            ]
        }
        
        Question types available:
        - multiple_choice: 4 options with 1 correct
        - short_answer: Open-ended question requiring text response
        - fill_blank: Remove key terms for user to fill in
        - blur_processing: Identify key concepts that should be blurred
        """
        
        user_message = f"""
        Generate {count} questions for this learning content:
        
        Title: {content.title}
        Content: {content_text}
        
        Question types requested: {', '.join(question_types)}
        Difficulty level: {difficulty} (1=easy, 5=very hard)
        
        Focus on key concepts and ensure questions help reinforce learning through spaced repetition.
        """
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response_content, processing_time = self._make_api_call(messages, temperature=0.8, max_tokens=1500)
            
            # Parse JSON response with fallback handling
            try:
                response_data = json.loads(response_content)
                questions = response_data.get('questions', [])
            except json.JSONDecodeError:
                # Fallback: try to extract JSON from response (AI sometimes wraps JSON in text)
                try:
                    # Find JSON block in response by locating braces
                    start = response_content.find('{')
                    end = response_content.rfind('}') + 1
                    if start != -1 and end > start:
                        json_str = response_content[start:end]
                        response_data = json.loads(json_str)
                        questions = response_data.get('questions', [])
                    else:
                        raise AIServiceError("No valid JSON found in response")
                except json.JSONDecodeError:
                    raise AIServiceError("Failed to parse AI response as JSON")
            
            # Add metadata to questions for tracking and debugging
            for question in questions:
                question['ai_model_used'] = self.model
                question['processing_time_ms'] = processing_time
                question['generation_prompt'] = user_message
            
            # Cache the result to improve performance for repeated requests
            cache.set(cache_key, questions, self.cache_timeout)
            
            return questions
            
        except AIServiceError:
            raise
        except Exception as e:
            raise AIServiceError(f"Question generation failed: {str(e)}")
    
    def evaluate_answer(self, question: AIQuestion, user_answer: str) -> Dict[str, Any]:
        """
        Evaluate a user's answer using AI
        
        Args:
            question: AIQuestion object
            user_answer: User's answer to evaluate
        
        Returns:
            Dictionary with evaluation results
        """
        system_message = """You are an educational AI that evaluates student answers fairly and constructively.
        
        Return your response as valid JSON with this structure:
        {
            "score": 0.85,
            "feedback": "Detailed feedback on the answer",
            "similarity_score": 0.90,
            "evaluation_details": {
                "strengths": ["What the student got right"],
                "weaknesses": ["Areas for improvement"],
                "suggestions": ["How to improve"]
            }
        }
        
        Scoring guidelines:
        - 0.9-1.0: Excellent, complete understanding
        - 0.7-0.8: Good, mostly correct with minor issues
        - 0.5-0.6: Partial understanding, some correct elements
        - 0.3-0.4: Basic understanding but significant gaps
        - 0.0-0.2: Incorrect or no understanding shown
        """
        
        user_message = f"""
        Evaluate this student answer:
        
        Question: {question.question_text}
        Question Type: {question.question_type.display_name}
        Expected Answer: {question.correct_answer}
        Student Answer: {user_answer}
        
        Consider:
        1. Accuracy of the information
        2. Completeness of the response
        3. Understanding demonstrated
        4. Semantic similarity to correct answer
        
        Provide constructive feedback that helps the student learn.
        """
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response_content, processing_time = self._make_api_call(messages, temperature=0.3, max_tokens=800)
            
            # Parse JSON response
            try:
                evaluation_data = json.loads(response_content)
            except json.JSONDecodeError:
                # Fallback parsing
                try:
                    start = response_content.find('{')
                    end = response_content.rfind('}') + 1
                    if start != -1 and end > start:
                        json_str = response_content[start:end]
                        evaluation_data = json.loads(json_str)
                    else:
                        raise AIServiceError("No valid JSON found in response")
                except json.JSONDecodeError:
                    raise AIServiceError("Failed to parse AI response as JSON")
            
            # Validate and normalize score to ensure data integrity
            score = evaluation_data.get('score', 0.0)
            if not isinstance(score, (int, float)) or score < 0 or score > 1:
                score = 0.5  # Default to neutral score if invalid
            
            # Add metadata for tracking
            evaluation_data['score'] = float(score)
            evaluation_data['ai_model_used'] = self.model
            evaluation_data['processing_time_ms'] = processing_time
            
            return evaluation_data
            
        except AIServiceError:
            raise
        except Exception as e:
            raise AIServiceError(f"Answer evaluation failed: {str(e)}")
    
    def generate_fill_blanks(self, content_text: str, num_blanks: int = 3) -> Dict[str, Any]:
        """
        Generate fill-in-the-blank questions by identifying key terms to remove
        
        Args:
            content_text: Text content to process
            num_blanks: Number of blanks to create
        
        Returns:
            Dictionary with blanked text and answers
        """
        system_message = """You are an AI that creates fill-in-the-blank exercises.
        
        Return your response as valid JSON:
        {
            "blanked_text": "Text with [BLANK_1], [BLANK_2], etc.",
            "answers": {
                "BLANK_1": "first answer",
                "BLANK_2": "second answer"
            },
            "keywords": ["key", "terms", "removed"]
        }
        """
        
        user_message = f"""
        Create {num_blanks} fill-in-the-blank questions from this text:
        
        {content_text[:1500]}
        
        Replace key terms with [BLANK_1], [BLANK_2], etc.
        Choose important concepts that test understanding.
        """
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response_content, processing_time = self._make_api_call(messages)
            
            # Parse response and add metadata
            try:
                result = json.loads(response_content)
                result['ai_model_used'] = self.model
                result['processing_time_ms'] = processing_time
                return result
            except json.JSONDecodeError:
                raise AIServiceError("Failed to parse fill-blank response")
                
        except Exception as e:
            raise AIServiceError(f"Fill-blank generation failed: {str(e)}")
    
    def identify_blur_regions(self, content_text: str) -> Dict[str, Any]:
        """
        Identify regions of text that should be blurred for review
        
        Args:
            content_text: Text content to analyze
        
        Returns:
            Dictionary with blur regions and metadata
        """
        system_message = """You are an AI that identifies key concepts for blur processing in educational content.
        
        Return your response as valid JSON:
        {
            "blur_regions": [
                {
                    "text": "text to blur",
                    "start_pos": 10,
                    "end_pos": 20,
                    "importance": 0.9,
                    "concept_type": "definition"
                }
            ],
            "concepts": ["key concepts identified"]
        }
        """
        
        user_message = f"""
        Identify 3-5 key text regions to blur in this educational content:
        
        {content_text[:1500]}
        
        Focus on:
        - Key definitions
        - Important facts
        - Critical concepts
        - Essential formulas or terms
        """
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response_content, processing_time = self._make_api_call(messages)
            
            # Parse response and add tracking metadata
            try:
                result = json.loads(response_content)
                result['ai_model_used'] = self.model
                result['processing_time_ms'] = processing_time
                return result
            except json.JSONDecodeError:
                raise AIServiceError("Failed to parse blur regions response")
                
        except Exception as e:
            raise AIServiceError(f"Blur region identification failed: {str(e)}")
    
    def chat_about_content(self, content_text: str, content_title: str, user_message: str) -> Dict[str, Any]:
        """
        Provide AI tutoring by answering questions about specific content
        
        Args:
            content_text: The learning content text
            content_title: Title of the content
            user_message: User's question
        
        Returns:
            Dictionary with AI response and metadata
        """
        system_message = f"""You are an AI tutor helping a student understand the learning material titled "{content_title}".

        Learning Material:
        {content_text[:2000]}  # Limit content to prevent token overflow

        Guidelines:
        - Answer questions based on the provided learning material
        - If the question is not related to the material, gently redirect to the content
        - Provide clear, educational explanations
        - Use examples when helpful
        - Encourage further learning
        - Be supportive and patient
        - Answer in Korean
        """
        
        user_prompt = f"""
        Student Question: {user_message}
        
        Please provide a helpful answer based on the learning material about "{content_title}".
        """
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt}
        ]
        
        try:
            response_content, processing_time = self._make_api_call(messages, temperature=0.7, max_tokens=500)
            
            return {
                "message": user_message,
                "response": response_content,
                "content_title": content_title,
                "ai_model_used": self.model,
                "processing_time_ms": processing_time
            }
            
        except Exception as e:
            raise AIServiceError(f"AI chat failed: {str(e)}")


# Singleton instance
ai_service = OpenAIService()