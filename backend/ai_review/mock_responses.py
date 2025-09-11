"""
AI Mock Responses for Development and Testing
"""
import json
import random
from typing import Dict, List, Any


class AIMockResponses:
    """
    Provides mock responses for AI services during development and testing
    """
    
    @staticmethod
    def get_weekly_test_list_response() -> Dict[str, Any]:
        """Mock response for weekly test list"""
        return {
            "tests": [
                {
                    "id": 1,
                    "name": "기본 문법 테스트",
                    "description": "기본적인 문법 사항을 확인하는 테스트입니다.",
                    "question_count": 10,
                    "estimated_time": "15분",
                    "difficulty": "EASY",
                    "created_at": "2024-01-15T09:00:00Z"
                },
                {
                    "id": 2, 
                    "name": "심화 이해도 테스트",
                    "description": "심화된 내용의 이해도를 측정하는 테스트입니다.",
                    "question_count": 15,
                    "estimated_time": "25분",
                    "difficulty": "MEDIUM",
                    "created_at": "2024-01-14T14:30:00Z"
                }
            ]
        }
    
    @staticmethod
    def get_weekly_test_response(test_type: str = "create") -> Dict[str, Any]:
        """Mock response for weekly test creation/start"""
        if test_type == "create":
            return {
                "test_id": random.randint(1000, 9999),
                "name": "주간 복습 테스트",
                "description": "이번 주에 학습한 내용을 복습하는 테스트입니다.",
                "questions": [
                    {
                        "id": 1,
                        "question_text": "다음 중 올바른 설명은?",
                        "question_type": "MULTIPLE_CHOICE",
                        "choices": ["선택지 1", "선택지 2", "선택지 3", "선택지 4"],
                        "correct_answer": "선택지 2",
                        "difficulty": "MEDIUM",
                        "points": 10
                    }
                ],
                "total_questions": 10,
                "estimated_time": "20분"
            }
        else:  # start
            return {
                "session_id": f"test_session_{random.randint(10000, 99999)}",
                "current_question": 1,
                "total_questions": 10,
                "question": {
                    "id": 1,
                    "question_text": "첫 번째 문제입니다. 다음 중 올바른 것은?",
                    "question_type": "MULTIPLE_CHOICE",
                    "choices": ["A", "B", "C", "D"],
                    "time_limit": 60
                }
            }
    
    @staticmethod
    def get_adaptive_test_response(test_type: str = "start", difficulty: str = "MEDIUM") -> Dict[str, Any]:
        """Mock response for adaptive difficulty test"""
        if test_type == "start":
            return {
                "session_id": f"adaptive_session_{random.randint(10000, 99999)}",
                "initial_difficulty": difficulty,
                "current_question": 1,
                "question": {
                    "id": 1,
                    "question_text": f"{difficulty} 난이도 문제입니다. 다음 중 올바른 것은?",
                    "question_type": "MULTIPLE_CHOICE",
                    "choices": ["옵션 1", "옵션 2", "옵션 3", "옵션 4"],
                    "difficulty": difficulty,
                    "time_limit": 90
                }
            }
        else:  # answer
            return {
                "is_correct": random.choice([True, False]),
                "next_difficulty": random.choice(["EASY", "MEDIUM", "HARD"]),
                "next_question": {
                    "id": 2,
                    "question_text": "다음 문제입니다.",
                    "question_type": "MULTIPLE_CHOICE", 
                    "choices": ["답변 1", "답변 2", "답변 3", "답변 4"],
                    "time_limit": 90
                },
                "feedback": "좋은 답변입니다!"
            }
    
    @staticmethod
    def get_question_generation_response(
        content_text: str, 
        question_type: str = "MULTIPLE_CHOICE",
        difficulty: str = "MEDIUM",
        count: int = 1
    ) -> Dict[str, Any]:
        """Mock response for question generation"""
        questions = []
        for i in range(count):
            if question_type == "MULTIPLE_CHOICE":
                question = {
                    "question_text": f"[{difficulty}] {content_text[:50]}...에 관한 문제 {i+1}번입니다.",
                    "question_type": "MULTIPLE_CHOICE",
                    "choices": [
                        "첫 번째 선택지",
                        "두 번째 선택지", 
                        "세 번째 선택지",
                        "네 번째 선택지"
                    ],
                    "correct_answer": "두 번째 선택지",
                    "explanation": "이것이 정답인 이유는...",
                    "difficulty": difficulty,
                    "estimated_time": 60
                }
            elif question_type == "SHORT_ANSWER":
                question = {
                    "question_text": f"[{difficulty}] {content_text[:50]}...에 대해 간략히 설명하세요.",
                    "question_type": "SHORT_ANSWER",
                    "correct_answer": "예시 답변입니다.",
                    "explanation": "이런 내용이 포함되어야 합니다.",
                    "difficulty": difficulty,
                    "estimated_time": 120
                }
            else:  # ESSAY
                question = {
                    "question_text": f"[{difficulty}] {content_text[:50]}...에 대한 당신의 견해를 자세히 서술하세요.",
                    "question_type": "ESSAY",
                    "correct_answer": "다양한 관점에서 접근할 수 있는 문제입니다.",
                    "explanation": "다음과 같은 요소들을 고려해보세요.",
                    "difficulty": difficulty,
                    "estimated_time": 300
                }
            questions.append(question)
        
        return {
            "questions": questions,
            "generated_count": len(questions),
            "content_analysis": {
                "topic": "추출된 주제",
                "key_concepts": ["개념1", "개념2", "개념3"],
                "difficulty_level": difficulty
            }
        }
    
    @staticmethod
    def get_answer_evaluation_response(
        question_text: str,
        correct_answer: str,
        user_answer: str,
        question_type: str = "MULTIPLE_CHOICE"
    ) -> Dict[str, Any]:
        """Mock response for answer evaluation"""
        # Simple mock logic
        is_correct = user_answer.lower().strip() == correct_answer.lower().strip()
        
        return {
            "is_correct": is_correct,
            "score": 100 if is_correct else random.randint(30, 80),
            "max_score": 100,
            "feedback": {
                "summary": "정답입니다!" if is_correct else "틀렸지만 부분적으로 맞는 내용이 있습니다.",
                "detailed_feedback": "좋은 답변입니다. 핵심을 잘 파악했습니다." if is_correct else "다시 한번 검토해보세요.",
                "improvement_suggestions": [] if is_correct else ["개념을 다시 정리해보세요", "예시를 더 찾아보세요"],
                "strengths": ["논리적 구성", "핵심 파악"] if is_correct else ["노력하는 자세"],
                "weaknesses": [] if is_correct else ["개념 이해 부족", "세부사항 놓침"]
            },
            "correct_answer_explanation": f"정답은 '{correct_answer}'입니다. 그 이유는...",
            "related_concepts": ["관련 개념 1", "관련 개념 2"],
            "difficulty_assessment": "적절한 수준"
        }
    
    @staticmethod
    def get_chat_response(
        content_text: str,
        content_title: str, 
        user_message: str,
        conversation_history: List[Dict] = None
    ) -> Dict[str, Any]:
        """Mock response for AI chat"""
        return {
            "response": f"'{content_title}'에 대한 질문이군요! '{user_message}'에 대해 답변드리겠습니다. 이는 중요한 개념으로...",
            "response_type": "INFORMATIVE",
            "confidence": random.uniform(0.8, 0.95),
            "sources": [
                {
                    "type": "content",
                    "title": content_title,
                    "relevance": 0.9
                }
            ],
            "suggested_follow_ups": [
                "이와 관련된 다른 개념은 무엇인가요?",
                "실제 예시를 들어주실 수 있나요?",
                "이것을 어떻게 응용할 수 있을까요?"
            ],
            "session_id": f"chat_session_{random.randint(1000, 9999)}"
        }
    
    @staticmethod
    def get_content_analysis_response(content_text: str, content_title: str) -> Dict[str, Any]:
        """Mock response for content analysis"""
        return {
            "analysis": {
                "main_topics": ["주제 1", "주제 2", "주제 3"],
                "key_concepts": ["핵심 개념 A", "핵심 개념 B", "핵심 개념 C"],
                "difficulty_level": "MEDIUM",
                "estimated_reading_time": f"{len(content_text) // 200 + 1}분",
                "content_type": "이론",
                "prerequisites": ["기초 개념", "선수 지식"]
            },
            "quality_score": {
                "overall": random.randint(75, 95),
                "clarity": random.randint(80, 95),
                "completeness": random.randint(70, 90),
                "accuracy": random.randint(85, 98)
            },
            "suggestions": [
                "예시를 더 추가하면 좋을 것 같습니다",
                "도표나 그림을 포함하면 이해가 쉬워질 것입니다",
                "연습 문제를 추가해보세요"
            ],
            "learning_objectives": [
                "이 내용을 통해 학습자는 X를 이해할 수 있습니다",
                "Y에 대한 개념을 정립할 수 있습니다",
                "Z를 적용할 수 있게 됩니다"
            ]
        }