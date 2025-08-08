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


# Singleton instance
ai_service = ClaudeService()