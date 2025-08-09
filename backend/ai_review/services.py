"""
AI service integration for question generation and answer evaluation using Claude
"""
import anthropic
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


class ClaudeService:
    """
    Claude service for question generation and answer evaluation
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
        self.model = getattr(settings, 'CLAUDE_MODEL', 'claude-3-haiku-20240307')
        self.max_retries = getattr(settings, 'AI_MAX_RETRIES', 3)
        self.cache_timeout = getattr(settings, 'AI_CACHE_TIMEOUT', 3600)  # 1 hour
    
    def _make_api_call(self, messages: List[Dict], temperature: float = 0.7, max_tokens: int = 1000) -> Tuple[str, int]:
        """
        Make an API call to Claude with retry logic
        
        Returns:
            Tuple[str, int]: (response_content, processing_time_ms)
        """
        if not self.client.api_key:
            raise AIServiceError("Claude API key not configured")
        
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
    
    def evaluate_question_quality(self, question_data: Dict, content_text: str) -> Dict:
        """
        AI가 생성한 문제의 품질을 자동으로 평가
        """
        system_message = """You are an educational expert evaluating the quality of learning questions.

Rate each question on a scale of 1-10 for:
1. CLARITY: Is the question clear and unambiguous?
2. EDUCATIONAL_VALUE: Does it test important concepts?
3. DIFFICULTY_APPROPRIATENESS: Is the difficulty level appropriate?
4. DISTRACTOR_QUALITY: Are wrong answers plausible but clearly incorrect?

Respond with JSON:
{
    "overall_score": 8.5,
    "clarity": 9,
    "educational_value": 8,
    "difficulty_appropriateness": 8,
    "distractor_quality": 9,
    "feedback": "Specific suggestions for improvement",
    "approved": true
}

A question needs overall_score >= 7.0 to be approved."""

        user_message = f"""
        LEARNING CONTENT:
        {content_text[:1000]}
        
        QUESTION TO EVALUATE:
        Type: {question_data.get('question_type')}
        Question: {question_data.get('question_text')}
        Correct Answer: {question_data.get('correct_answer')}
        Options: {question_data.get('options', [])}
        Explanation: {question_data.get('explanation', '')}
        
        Please evaluate this question's quality and educational effectiveness.
        """
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response_content, _ = self._make_api_call(messages, temperature=0.3, max_tokens=500)
            return json.loads(response_content)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Question quality evaluation failed: {e}")
            return {"overall_score": 5.0, "approved": False, "feedback": "Evaluation failed"}

    def analyze_content_structure(self, content_text: str, title: str) -> Dict:
        """
        학습 내용의 구조를 분석하여 더 정교한 문제 생성을 위한 정보 추출
        """
        system_message = """You are an educational content analyst. Analyze learning content to identify its structure and key elements for question generation.

Respond with JSON:
{
    "content_type": "concept|procedure|fact|principle|example",
    "key_concepts": ["concept1", "concept2", "concept3"],
    "definitions": ["term: definition"],
    "examples": ["example descriptions"],
    "prerequisites": ["required prior knowledge"],
    "learning_objectives": ["what students should learn"],
    "difficulty_indicators": ["factors that make this content challenging"],
    "question_opportunities": {
        "multiple_choice": ["concept areas suitable for MC questions"],
        "fill_blank": ["key terms that could be blanked"],
        "blur_processing": ["visual/conceptual elements to blur"]
    }
}"""

        user_message = f"""
        CONTENT TO ANALYZE:
        Title: {title}
        Content: {content_text}
        
        Please analyze this learning content structure for optimal question generation.
        Focus on identifying the most important concepts that students need to understand and remember.
        """
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response_content, _ = self._make_api_call(messages, temperature=0.3, max_tokens=800)
            return json.loads(response_content)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Content analysis failed: {e}")
            return {
                "content_type": "concept",
                "key_concepts": [],
                "question_opportunities": {"multiple_choice": [], "fill_blank": [], "blur_processing": []}
            }

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
        
        # Analyze content structure first for better question generation
        content_analysis = self.analyze_content_structure(content_text, content.title)
        
        system_message = """You are an expert educational AI specialized in creating pedagogically sound questions for spaced repetition learning, following Bloom's Taxonomy principles.

COGNITIVE LEVELS (Bloom's Taxonomy):
- Level 1-2 (Remember/Understand): Recall facts, explain concepts
- Level 3 (Apply): Use knowledge in new situations  
- Level 4 (Analyze): Break down information, find patterns
- Level 5 (Evaluate/Create): Judge quality, synthesize new ideas

QUESTION QUALITY STANDARDS:
- Test understanding, not just memorization
- Use precise, unambiguous language
- Create plausible but clearly wrong distractors
- Focus on transferable core concepts
- Align difficulty with cognitive level

Always respond with valid JSON in this exact structure:
{
    "questions": [
        {
            "question_type": "multiple_choice",
            "question_text": "Clear, specific question?",
            "correct_answer": "The correct answer",
            "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
            "explanation": "Why this answer is correct and others are wrong",
            "keywords": ["key", "terms", "concept"],
            "cognitive_level": "understand|apply|analyze|evaluate",
            "learning_objective": "What students should achieve"
        }
    ]
}

QUESTION TYPES:
- multiple_choice: 4 options, 1 correct. Distractors should be common misconceptions
- fill_blank: Remove KEY concepts that test understanding, not trivial details  
- blur_processing: Identify concepts crucial for comprehension"""
        
        # Map difficulty to cognitive levels
        cognitive_mapping = {
            1: "remember - recall basic facts and definitions",
            2: "understand - explain concepts in your own words", 
            3: "apply - use knowledge to solve problems",
            4: "analyze - break down complex ideas and find relationships",
            5: "evaluate - judge quality and make reasoned decisions"
        }
        
        user_message = f"""
        CONTENT TO ANALYZE:
        Title: {content.title}
        Content: {content_text}
        
        CONTENT ANALYSIS RESULTS:
        Content Type: {content_analysis.get('content_type', 'concept')}
        Key Concepts: {', '.join(content_analysis.get('key_concepts', []))}
        Learning Objectives: {', '.join(content_analysis.get('learning_objectives', []))}
        Prerequisites: {', '.join(content_analysis.get('prerequisites', []))}
        
        REQUIREMENTS:
        - Generate {count} high-quality questions
        - Question types: {', '.join(question_types)}
        - Cognitive level: {cognitive_mapping.get(difficulty, 'understand')}
        - Target Korean learners (use Korean for questions and explanations)
        
        STRATEGIC FOCUS:
        1. Prioritize the identified key concepts: {', '.join(content_analysis.get('key_concepts', [])[:3])}
        2. Test {cognitive_mapping.get(difficulty, 'understand')} level understanding
        3. For multiple choice: Use misconceptions as distractors, focus on {content_analysis.get('question_opportunities', {}).get('multiple_choice', [])}
        4. For fill-blank: Target these key terms: {content_analysis.get('question_opportunities', {}).get('fill_blank', [])}
        5. Ensure questions support long-term retention through spaced repetition
        
        QUALITY VALIDATION:
        - Do questions align with the learning objectives?
        - Are they appropriate for the content type ({content_analysis.get('content_type', 'concept')})?
        - Will they help students master the prerequisites for advanced topics?
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
            
            # Quality evaluation and filtering
            approved_questions = []
            for question in questions:
                # Add generation metadata
                question['ai_model_used'] = self.model
                question['processing_time_ms'] = processing_time
                question['generation_prompt'] = user_message
                
                # Evaluate question quality
                quality_eval = self.evaluate_question_quality(question, content_text)
                question['quality_score'] = quality_eval.get('overall_score', 5.0)
                question['quality_feedback'] = quality_eval.get('feedback', '')
                question['auto_approved'] = quality_eval.get('approved', False)
                
                # Only include high-quality questions
                if quality_eval.get('approved', False):
                    approved_questions.append(question)
                else:
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Question rejected due to low quality: {quality_eval.get('feedback')}")
            
            # If not enough approved questions, generate more
            if len(approved_questions) < count and len(approved_questions) > 0:
                import logging
                logger = logging.getLogger(__name__)
                logger.info(f"Generated {len(approved_questions)}/{count} approved questions")
            
            # Cache the approved results
            cache.set(cache_key, approved_questions, self.cache_timeout)
            
            return approved_questions
            
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
        system_message = """You are an AI assistant specialized in creating educational fill-in-the-blank exercises.

Your task is to analyze text and strategically remove key terms to create effective learning exercises.

Respond with valid JSON in this exact format:
{
    "blanked_text": "Original text with [BLANK_1], [BLANK_2], etc. replacing key terms",
    "answers": {
        "BLANK_1": "first removed term",
        "BLANK_2": "second removed term"
    },
    "keywords": ["important", "concepts", "from", "text"]
}

Guidelines for creating blanks:
- Choose terms that are central to understanding the concept
- Prefer nouns, key adjectives, and specific technical terms
- Avoid removing common words like articles, prepositions, or conjunctions  
- Ensure the remaining text provides sufficient context
- Space blanks throughout the text rather than clustering them
- Select terms that test comprehension, not just memory"""
        
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
        system_message = f"""You are a knowledgeable and patient AI tutor helping a student understand the learning material titled "{content_title}".

Learning Material Context:
{content_text[:2000]}

Your role:
- Provide clear, educational explanations based on the learning material
- Use examples and analogies when they help understanding
- Break down complex concepts into simpler parts
- Encourage questions and deeper exploration
- If asked about topics outside the material, politely redirect to the content
- Be supportive and maintain a positive learning environment
- Respond in Korean for Korean speakers, English for others

Teaching approach:
- Start with core concepts before details
- Use the Socratic method when appropriate
- Provide practical applications when relevant
- Acknowledge when something might be challenging"""
        
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
    
    def evaluate_explanation(self, content, user_explanation):
        """Evaluate user's descriptive explanation of content with intelligent content quality assessment"""
        system_message = """
당신은 교육 평가 전문가이자 내용 분석 전문가입니다. 다음 두 가지를 수행해주세요:

1) 먼저 원본 학습 내용의 품질을 판단하세요:
- 내용이 명확하고 이해하기 쉬운가?
- 개념이 논리적으로 구성되어 있는가?
- 학습 목적에 적합한 내용인가?
- 내용이 부족하거나 애매한 부분이 있는가?

2) 원본 내용의 품질을 고려하여 학습자의 설명을 평가하세요:

평가 기준:
- 원본 내용이 우수한 경우: 엄격한 기준 적용 (핵심 개념 60%, 완성도 25%, 논리성 15%)
- 원본 내용이 보통인 경우: 표준 기준 적용 (핵심 개념 50%, 완성도 30%, 논리성 20%)  
- 원본 내용이 부족한 경우: 관대한 기준 적용 (이해 노력 70%, 자신만의 해석 30%)

특별 고려사항:
- 원본이 애매하거나 불완전하면 학습자의 나름의 이해와 해석을 높이 평가
- 원본에서 설명이 부족한 부분을 학습자가 보완했다면 가산점
- 원본이 너무 간단하거나 추상적이면 구체적 예시나 경험을 추가한 것을 긍정 평가
- 학습자가 원본의 한계를 인식하고 추가 설명을 시도한 경우 우수 평가

응답은 반드시 다음 JSON 형식으로 제공하세요:
{
  "content_quality_assessment": {
    "quality_level": "excellent|good|average|poor",
    "clarity": 85,
    "completeness": 75,
    "logical_structure": 90,
    "content_issues": ["문제점1", "문제점2"],
    "content_strengths": ["장점1", "장점2"]
  },
  "evaluation_approach": "strict|standard|lenient",
  "score": 85,
  "feedback": "원본 내용의 품질을 고려한 구체적인 피드백",
  "strengths": ["학습자의 강점1", "강점2"],
  "improvements": ["개선 제안1", "개선 제안2"],
  "key_concepts_covered": ["이해한 개념1", "개념2"],
  "missing_concepts": ["놓친 개념1", "개념2"],
  "bonus_points": ["원본을 보완한 부분", "추가 통찰"],
  "adaptation_note": "원본 내용 품질에 따른 평가 조정 설명"
}

점수는 0-100 사이의 정수로, 원본 내용 품질에 따라 유연하게 조정하세요.
- 원본이 훌륭하면 80점도 높은 점수
- 원본이 부족하면 학습자의 노력을 인정하여 관대하게 평가
"""

        user_message = f"""
=== 평가할 원본 학습 내용 ===
제목: {content.title}
내용: {content.content}

=== 학습자의 서술형 설명 ===
{user_explanation}

=== 평가 지시사항 ===
1. 먼저 원본 학습 내용의 품질을 객관적으로 분석하세요
2. 원본 내용의 품질 수준에 맞는 평가 기준을 적용하세요
3. 학습자가 원본의 부족한 부분을 보완했는지 확인하세요
4. 대충 작성된 원본에 대해서도 학습자가 나름의 이해를 보여주면 격려하세요
5. 원본이 우수하다면 더 높은 기준을 적용하되, 너무 가혹하지는 않게 하세요
"""

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response_content, processing_time = self._make_api_call(messages, temperature=0.3, max_tokens=1500)
            
            # Parse JSON response
            try:
                evaluation_data = json.loads(response_content)
                
                # Extract content quality assessment
                content_assessment = evaluation_data.get('content_quality_assessment', {})
                
                return {
                    'score': evaluation_data.get('score', 0),
                    'feedback': evaluation_data.get('feedback', '평가를 완료했습니다.'),
                    'strengths': evaluation_data.get('strengths', []),
                    'improvements': evaluation_data.get('improvements', []),
                    'key_concepts_covered': evaluation_data.get('key_concepts_covered', []),
                    'missing_concepts': evaluation_data.get('missing_concepts', []),
                    'bonus_points': evaluation_data.get('bonus_points', []),
                    'evaluation_approach': evaluation_data.get('evaluation_approach', 'standard'),
                    'adaptation_note': evaluation_data.get('adaptation_note', ''),
                    'content_quality_assessment': {
                        'quality_level': content_assessment.get('quality_level', 'average'),
                        'clarity': content_assessment.get('clarity', 70),
                        'completeness': content_assessment.get('completeness', 70),
                        'logical_structure': content_assessment.get('logical_structure', 70),
                        'content_issues': content_assessment.get('content_issues', []),
                        'content_strengths': content_assessment.get('content_strengths', [])
                    },
                    'ai_model_used': self.model,
                    'processing_time_ms': processing_time,
                    'content_title': content.title
                }
            except json.JSONDecodeError:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to parse explanation evaluation JSON response: {response_content}")
                # Fallback response with smart content quality detection
                content_length = len(content.content.strip())
                is_short_content = content_length < 100
                
                return {
                    'score': 65 if is_short_content else 50,
                    'feedback': f'설명을 검토했습니다. {"원본 내용이 간단하여 관대하게 평가했습니다" if is_short_content else "AI 파싱 오류로 인해 기본 점수를 부여합니다"}.',
                    'strengths': ['설명을 작성해주셨습니다', '학습에 대한 노력을 보여주셨습니다'],
                    'improvements': ['더 구체적인 설명을 추가해보세요', '예시나 경험을 포함해보세요'],
                    'key_concepts_covered': [],
                    'missing_concepts': [],
                    'bonus_points': [],
                    'evaluation_approach': 'lenient' if is_short_content else 'standard',
                    'adaptation_note': '원본 내용 분석 중 오류가 발생하여 기본 평가를 적용했습니다.',
                    'content_quality_assessment': {
                        'quality_level': 'poor' if is_short_content else 'average',
                        'clarity': 50,
                        'completeness': 40 if is_short_content else 60,
                        'logical_structure': 60,
                        'content_issues': ['AI 분석 실패'],
                        'content_strengths': ['기본 정보 포함']
                    },
                    'ai_model_used': self.model,
                    'processing_time_ms': processing_time,
                    'content_title': content.title
                }
                
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error evaluating explanation: {str(e)}")
            raise AIServiceError(f"Explanation evaluation failed: {str(e)}")
    
    def generate_weekly_test(self, user, week_contents, difficulty_distribution=None):
        """
        주간 학습 콘텐츠를 기반으로 종합 시험 생성
        
        Args:
            user: 사용자 객체
            week_contents: 주간 학습한 콘텐츠 목록
            difficulty_distribution: 난이도 분포 (기본값: easy 30%, medium 50%, hard 20%)
        
        Returns:
            생성된 시험 문제 목록
        """
        if not difficulty_distribution:
            difficulty_distribution = {
                'easy': 5,    # 30%
                'medium': 8,  # 50%
                'hard': 3     # 20%
            }
        
        system_message = """You are an expert educational AI creating comprehensive weekly tests.

Create a balanced test that:
1. Covers all major topics from the week
2. Tests different cognitive levels (recall, understanding, application)
3. Provides fair difficulty distribution
4. Avoids repetition of similar concepts
5. Includes diverse question types

Focus on:
- Key concepts that connect multiple topics
- Practical applications of learned material
- Critical thinking questions
- Common misconceptions to test understanding

Respond with valid JSON:
{
    "test_questions": [
        {
            "content_id": "content_id",
            "question_type": "multiple_choice|fill_blank|explanation",
            "difficulty": 1-5,
            "question_text": "Question text",
            "correct_answer": "Answer",
            "options": ["A", "B", "C", "D"],
            "explanation": "Why this matters",
            "estimated_time_seconds": 60,
            "topic_coverage": ["topic1", "topic2"],
            "cognitive_level": "recall|understand|apply|analyze"
        }
    ],
    "test_overview": {
        "total_topics_covered": 10,
        "estimated_total_minutes": 30,
        "difficulty_balance": "Appropriate for user level"
    }
}"""
        
        # 콘텐츠 요약 준비
        content_summaries = []
        for content in week_contents[:10]:  # 최대 10개 콘텐츠
            summary = f"Title: {content.title}\nCategory: {content.category}\nKey points: {content.content[:200]}..."
            content_summaries.append(summary)
        
        user_message = f"""
        Create a comprehensive weekly test for this user's learning:
        
        USER PROFILE:
        - Subscription: {user.subscription.tier}
        - Weekly goal: {user.weekly_goal} reviews
        
        WEEK'S LEARNING CONTENT:
        {chr(10).join(content_summaries)}
        
        REQUIREMENTS:
        - Total questions: {sum(difficulty_distribution.values())}
        - Easy questions (difficulty 1-2): {difficulty_distribution.get('easy', 5)}
        - Medium questions (difficulty 3): {difficulty_distribution.get('medium', 8)}
        - Hard questions (difficulty 4-5): {difficulty_distribution.get('hard', 3)}
        
        GUIDELINES:
        - Mix question types for variety
        - Ensure comprehensive topic coverage
        - Questions should build on each other when possible
        - Include at least one question that connects multiple topics
        - Target completion time: 30-45 minutes
        """
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response_content, processing_time = self._make_api_call(messages, temperature=0.7, max_tokens=2000)
            
            result = json.loads(response_content)
            questions = result.get('test_questions', [])
            
            # 메타데이터 추가
            for question in questions:
                question['ai_model_used'] = self.model
                question['processing_time_ms'] = processing_time
                question['generation_context'] = 'weekly_test'
            
            return {
                'questions': questions,
                'overview': result.get('test_overview', {}),
                'processing_time_ms': processing_time
            }
            
        except Exception as e:
            logger.error(f"Weekly test generation failed: {str(e)}")
            raise AIServiceError(f"Failed to generate weekly test: {str(e)}")
    
    def perform_instant_check(self, content, check_point='current', question_count=3):
        """
        콘텐츠 학습 중 실시간 이해도 검토
        
        Args:
            content: 학습 중인 콘텐츠
            check_point: 검토 시점 (예: '50%', 'end', 'current')
            question_count: 생성할 문제 수 (1-5)
        
        Returns:
            빠른 체크 문제 및 평가 기준
        """
        system_message = """You are an AI tutor performing real-time comprehension checks.

Create quick, focused questions that:
1. Test immediate understanding of just-learned concepts
2. Are answerable in 30-60 seconds each
3. Provide instant feedback value
4. Identify specific misconceptions
5. Guide further learning needs

Respond with valid JSON:
{
    "check_questions": [
        {
            "question_type": "quick_choice|true_false|brief_answer",
            "question_text": "Quick check question",
            "correct_answer": "Answer",
            "options": ["A", "B", "C"] or null,
            "instant_feedback": {
                "correct": "Great! You understood that...",
                "incorrect": "Let's review: The key point is...",
                "partial": "You're on the right track, but..."
            },
            "concept_tested": "Specific concept being checked",
            "followup_hint": "Additional guidance if needed"
        }
    ],
    "understanding_indicators": {
        "strong_understanding": ["Concept A", "Concept B"],
        "needs_review": ["Concept C"],
        "recommended_action": "Continue to next section|Review this part|Try practice problems"
    }
}"""
        
        user_message = f"""
        Create {question_count} instant comprehension check questions for:
        
        CONTENT: {content.title}
        CHECK POINT: {check_point}
        
        CONTENT EXCERPT:
        {content.content[:1000]}
        
        REQUIREMENTS:
        - Super quick to answer (30-60 seconds each)
        - Test the most important concepts up to this point
        - Provide immediate, actionable feedback
        - Help identify if the learner should continue or review
        - Use simple, clear language
        - Focus on understanding, not memorization
        """
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response_content, processing_time = self._make_api_call(
                messages, 
                temperature=0.5, 
                max_tokens=1000
            )
            
            result = json.loads(response_content)
            
            return {
                'questions': result.get('check_questions', []),
                'indicators': result.get('understanding_indicators', {}),
                'processing_time_ms': processing_time,
                'check_point': check_point
            }
            
        except Exception as e:
            logger.error(f"Instant check generation failed: {str(e)}")
            raise AIServiceError(f"Failed to generate instant check: {str(e)}")
    
    def analyze_learning_patterns(self, user, period_data):
        """
        사용자의 학습 패턴을 분석하여 개인화된 인사이트 제공
        
        Args:
            user: 사용자 객체
            period_data: 기간별 학습 데이터
        
        Returns:
            학습 패턴 분석 결과 및 추천사항
        """
        system_message = """You are an AI learning analytics expert analyzing student learning patterns.

Analyze the data to provide:
1. Learning behavior patterns (time, frequency, consistency)
2. Performance trends and trajectories
3. Strength and weakness identification
4. Personalized improvement strategies
5. Predictive insights for future performance

Respond with valid JSON:
{
    "pattern_analysis": {
        "optimal_study_time": "Morning|Afternoon|Evening|Night",
        "consistency_score": 85,
        "learning_style": "Visual|Auditory|Kinesthetic|Mixed",
        "focus_duration": "Short bursts|Medium sessions|Long sessions",
        "retention_pattern": "Strong initial|Gradual decline|Stable"
    },
    "performance_insights": {
        "overall_trend": "Improving|Stable|Declining",
        "growth_rate": 15.5,
        "plateau_areas": ["Topics showing no improvement"],
        "breakthrough_moments": ["Significant improvements"]
    },
    "recommendations": {
        "immediate_actions": ["Action 1", "Action 2"],
        "long_term_strategies": ["Strategy 1", "Strategy 2"],
        "optimal_review_schedule": "Customized intervals",
        "focus_areas": ["Priority topics"]
    },
    "predictions": {
        "expected_improvement": "20% in 30 days",
        "mastery_timeline": "Estimated dates for topic mastery",
        "risk_areas": ["Topics at risk of forgetting"]
    }
}"""
        
        user_message = f"""
        Analyze learning patterns for this user:
        
        USER PROFILE:
        - Subscription: {user.subscription.tier}
        - Weekly goal: {user.weekly_goal}
        
        LEARNING DATA:
        {json.dumps(period_data, indent=2)}
        
        Please provide:
        1. Detailed pattern analysis
        2. Actionable insights
        3. Personalized recommendations
        4. Future performance predictions
        5. Specific areas for improvement
        """
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response_content, processing_time = self._make_api_call(
                messages, 
                temperature=0.4, 
                max_tokens=1500
            )
            
            result = json.loads(response_content)
            result['processing_time_ms'] = processing_time
            result['analysis_date'] = timezone.now().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"Learning pattern analysis failed: {str(e)}")
            raise AIServiceError(f"Failed to analyze learning patterns: {str(e)}")
    
    def provide_study_mate_guidance(self, user, content, struggle_point, user_level='intermediate'):
        """
        AI 스터디 메이트가 맞춤형 학습 가이드 제공
        
        Args:
            user: 사용자 객체
            content: 학습 콘텐츠
            struggle_point: 어려워하는 부분
            user_level: 사용자 수준
        
        Returns:
            단계별 가이드 및 힌트
        """
        system_message = f"""You are a patient, adaptive AI study mate helping a {user_level} level student.

Your approach:
1. Assess the specific struggle point
2. Break down complex concepts into manageable steps
3. Provide hints that guide discovery, not direct answers
4. Adapt explanation style to user level
5. Encourage and motivate throughout

Teaching principles:
- Use analogies and real-world examples
- Build on prior knowledge
- Provide scaffolding support
- Check understanding at each step
- Celebrate small victories

Respond with valid JSON:
{{
    "diagnosis": {{
        "struggle_type": "conceptual|procedural|factual",
        "root_cause": "Why they're struggling",
        "prerequisite_gaps": ["Missing knowledge"]
    }},
    "guided_explanation": {{
        "step_1": {{
            "explanation": "Simple explanation",
            "check_question": "Do you see how...",
            "hint_if_stuck": "Think about..."
        }},
        "step_2": {{...}}
    }},
    "adaptive_hints": [
        {{
            "level": 1,
            "hint": "Gentle nudge",
            "reveals": "10% of answer"
        }},
        {{
            "level": 2,
            "hint": "More specific guidance",
            "reveals": "30% of answer"
        }}
    ],
    "encouragement": "Personalized motivational message",
    "next_steps": "What to do after understanding this"
}}"""
        
        user_message = f"""
        Help this {user_level} student understand:
        
        CONTENT: {content.title}
        STRUGGLE POINT: {struggle_point}
        
        RELEVANT CONTENT:
        {content.content[:800]}
        
        Please provide:
        1. Step-by-step explanation adapted to their level
        2. Progressive hints (don't give away the answer)
        3. Encouraging tone throughout
        4. Check for understanding
        5. Connect to what they might already know
        """
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response_content, processing_time = self._make_api_call(
                messages, 
                temperature=0.7, 
                max_tokens=1200
            )
            
            result = json.loads(response_content)
            result['processing_time_ms'] = processing_time
            result['session_metadata'] = {
                'user_level': user_level,
                'content_id': content.id,
                'timestamp': timezone.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Study mate guidance failed: {str(e)}")
            raise AIServiceError(f"Failed to provide study guidance: {str(e)}")
    
    def generate_summary_note(self, content, summary_type='one_page', user_preferences=None):
        """
        콘텐츠의 AI 요약 노트 생성
        
        Args:
            content: 요약할 콘텐츠
            summary_type: 요약 형식
            user_preferences: 사용자 선호 설정
        
        Returns:
            생성된 요약 노트
        """
        summary_prompts = {
            'one_page': """Create a comprehensive one-page summary that captures all essential information in a scannable format. Use bullet points, numbered lists, and clear sections.""",
            'mind_map': """Create a mind map structure showing the relationships between concepts. Start with the central topic and branch out to subtopics, using indentation to show hierarchy.""",
            'key_points': """Extract and list only the most critical points that a student must remember. Focus on core concepts, important facts, and key takeaways.""",
            'cornell_notes': """Format as Cornell notes with: 1) Cue column (questions/keywords), 2) Note-taking area (main content), 3) Summary section (brief overview)."""
        }
        
        system_message = f"""You are an expert at creating effective study summaries for optimal learning and retention.

{summary_prompts.get(summary_type, summary_prompts['one_page'])}

Requirements:
1. Maintain academic accuracy while simplifying language
2. Highlight connections between concepts
3. Include memory aids (mnemonics, associations)
4. Add visual markers for importance (★ for critical, → for processes)
5. Keep it concise but complete

Respond with valid JSON:
{{
    "summary": {{
        "title": "Clear, descriptive title",
        "main_content": "Formatted summary content",
        "sections": [
            {{
                "heading": "Section name",
                "content": "Section content",
                "importance": "high|medium|low"
            }}
        ]
    }},
    "key_concepts": [
        {{
            "concept": "Term",
            "definition": "Clear definition",
            "example": "Practical example"
        }}
    ],
    "study_questions": [
        "Self-test question 1",
        "Self-test question 2"
    ],
    "visual_elements": {{
        "diagrams_suggested": ["Diagram description"],
        "charts_suggested": ["Chart description"]
    }},
    "quick_review": "2-3 sentence summary of entire content"
}}"""
        
        user_message = f"""
        Create a {summary_type} summary for:
        
        TITLE: {content.title}
        CATEGORY: {content.category}
        
        CONTENT TO SUMMARIZE:
        {content.content}
        
        USER PREFERENCES:
        {json.dumps(user_preferences) if user_preferences else 'Standard format'}
        
        Make it:
        - Visually organized
        - Easy to scan and review
        - Focused on retention
        - Suitable for spaced repetition review
        """
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ]
        
        try:
            response_content, processing_time = self._make_api_call(
                messages, 
                temperature=0.3, 
                max_tokens=2000
            )
            
            result = json.loads(response_content)
            
            # 요약 통계 추가
            summary_text = json.dumps(result.get('summary', {}))
            word_count = len(summary_text.split())
            compression_ratio = (1 - (word_count / len(content.content.split()))) * 100
            
            result['metadata'] = {
                'word_count': word_count,
                'compression_ratio': round(compression_ratio, 1),
                'processing_time_ms': processing_time,
                'summary_type': summary_type,
                'ai_model_used': self.model
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            raise AIServiceError(f"Failed to generate summary: {str(e)}")


# Singleton instance
ai_service = ClaudeService()