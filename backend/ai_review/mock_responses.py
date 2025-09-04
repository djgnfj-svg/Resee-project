"""
AI Mock Responses - 모든 AI 기능의 예시 응답
실제 AI 연동 전까지 사용할 샘플 데이터
"""
import random
from datetime import datetime, timedelta


class AIMockResponses:
    """AI 기능별 Mock 응답 생성기"""
    
    @staticmethod
    def get_question_generation_response(content_text="", question_type="multiple_choice", difficulty=3, count=2):
        """AI 문제 생성 mock 응답"""
        difficulty_level = ["easy", "medium", "hard"][min(difficulty-1, 2)]
        
        base_questions = [
            {
                "question_text": f"{content_text[:50]}...에서 가장 중요한 개념은 무엇인가요?" if content_text else "프로그래밍에서 가장 중요한 개념은?",
                "options": [
                    "함수형 프로그래밍의 순수 함수 개념",
                    "객체 지향 프로그래밍의 상속", 
                    "반복문의 효율적 사용",
                    "변수의 스코프 관리"
                ],
                "correct_answer": "함수형 프로그래밍의 순수 함수 개념",
                "explanation": "주어진 내용에서 함수형 프로그래밍의 순수 함수가 가장 핵심적인 개념으로 강조되었습니다.",
                "keywords": ["함수형", "순수함수"],
                "difficulty": difficulty
            },
            {
                "question_text": "코드 최적화에 가장 효과적인 방법은?",
                "options": [
                    "메모리 사용량 최소화",
                    "알고리즘 복잡도 개선",
                    "코드 가독성 향상",
                    "주석 추가"
                ],
                "correct_answer": "알고리즘 복잡도 개선",
                "explanation": "알고리즘 복잡도를 개선하는 것이 성능에 가장 큰 영향을 미칩니다.",
                "keywords": ["최적화", "알고리즘"],
                "difficulty": difficulty
            }
        ]
        
        if question_type == "multiple_choice":
            selected_questions = base_questions[:count]
            return {
                "questions": selected_questions
            }
        
        elif question_type == "fill_blank":
            return {
                "success": True,
                "questions": [
                    {
                        "id": 1,
                        "question": "React에서 상태 관리를 위해 _____ 훅을 사용합니다.",
                        "type": "fill_blank",
                        "correct_answers": ["useState", "usestate"],
                        "hints": ["상태를 설정하고 업데이트하는 데 사용되는 React 훅"],
                        "difficulty": "easy",
                        "estimated_time": 60
                    }
                ],
                "total_questions": 1,
                "estimated_total_time": 60
            }
        
        elif question_type == "blur_regions":
            return {
                "success": True,
                "blur_regions": [
                    {
                        "start_index": 45,
                        "end_index": 67,
                        "text": "함수형 프로그래밍",
                        "reason": "핵심 개념",
                        "importance": "high"
                    },
                    {
                        "start_index": 120,
                        "end_index": 135,
                        "text": "순수 함수",
                        "reason": "중요한 용어",
                        "importance": "medium"
                    }
                ],
                "total_regions": 2
            }

    @staticmethod
    def get_answer_evaluation_response(question_text="", correct_answer="", user_answer="", question_type="multiple_choice"):
        """AI 답안 평가 mock 응답"""
        is_correct = random.choice([True, True, False])  # 80% 정답률로 설정
        
        score = 0.9 if is_correct else 0.4
        feedback = "잘했습니다! 정답입니다." if is_correct else "아쉽지만 틀렸습니다. 다시 한 번 생각해보세요."
        
        return {
            "score": score,
            "feedback": feedback,
            "similarity_score": 0.85 if is_correct else 0.3,
            "evaluation_details": {
                "strengths": ["정확한 핵심 개념 이해"] if is_correct else [],
                "weaknesses": [] if is_correct else ["핵심 개념 이해 부족"],
                "suggestions": ["더 많은 예시를 학습해보세요"] if not is_correct else ["관련 고급 개념을 학습해보세요"]
            }
        }

    @staticmethod
    def get_chat_response(content_text="", content_title="", user_message=""):
        """AI 채팅 mock 응답"""
        if not user_message:
            response_text = "안녕하세요! 학습에 관해 어떤 도움이 필요하신가요? 🤔"
            suggestions = ["복습 계획 세우기", "학습 방법 추천", "개념 설명 요청"]
        else:
            response_text = f"'{user_message}'에 대해 설명드리겠습니다.\n\n'{content_title}' 내용을 바탕으로 답변드리면:\n\n이 개념은 학습에서 매우 중요한 부분입니다. 핵심은 다음과 같습니다:\n\n1. **기본 원리**: 체계적인 학습 방법 적용\n2. **실제 적용**: 지식을 실무에 활용\n3. **주의사항**: 단계별 학습이 중요함\n\n더 궁금한 점이 있으시면 언제든 말씀해 주세요! 💡"
            suggestions = ["관련 개념 학습", "실습 예제", "추가 질문"]
            
        return {
            "response": response_text,
            "helpful": True,
            "confidence_score": 0.9,
            "follow_up_suggestions": suggestions
        }

    @staticmethod
    def get_weekly_test_list_response():
        """주간 시험 목록 mock 응답"""
        return [
            {
                "id": 1,
                "week_start_date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
                "week_end_date": datetime.now().strftime("%Y-%m-%d"),
                "total_questions": 15,
                "completed_questions": 15,
                "correct_answers": 12,
                "score": 80,
                "time_limit_minutes": 30,
                "started_at": (datetime.now() - timedelta(days=2)).isoformat(),
                "completed_at": (datetime.now() - timedelta(days=2, hours=1)).isoformat(),
                "difficulty_distribution": {
                    "easy": 5,
                    "medium": 7,
                    "hard": 3
                },
                "content_coverage": [1, 2, 3, 4, 5],
                "weak_areas": ["알고리즘", "데이터베이스"],
                "improvement_from_last_week": 5.2,
                "status": "completed",
                "accuracy_rate": 80.0,
                "completion_rate": 100.0,
                "time_spent_minutes": 28,
                "created_at": (datetime.now() - timedelta(days=7)).isoformat()
            },
            {
                "id": 2,
                "week_start_date": datetime.now().strftime("%Y-%m-%d"),
                "week_end_date": (datetime.now() + timedelta(days=6)).strftime("%Y-%m-%d"),
                "total_questions": 12,
                "completed_questions": 0,
                "correct_answers": 0,
                "score": None,
                "time_limit_minutes": 45,
                "started_at": None,
                "completed_at": None,
                "difficulty_distribution": {
                    "easy": 4,
                    "medium": 6,
                    "hard": 2
                },
                "content_coverage": [2, 3, 4, 5, 6],
                "weak_areas": [],
                "improvement_from_last_week": None,
                "status": "ready",
                "accuracy_rate": 0.0,
                "completion_rate": 0.0,
                "time_spent_minutes": 0,
                "created_at": datetime.now().isoformat()
            }
        ]

    @staticmethod
    def get_weekly_test_response(test_type="create"):
        """주간 시험 mock 응답"""
        if test_type == "create":
            return {
                "success": True,
                "test": {
                    "id": random.randint(1, 1000),
                    "week_start_date": datetime.now().strftime("%Y-%m-%d"),
                    "week_end_date": (datetime.now() + timedelta(days=6)).strftime("%Y-%m-%d"),
                    "total_questions": 10,
                    "time_limit_minutes": 30,
                    "difficulty_distribution": {
                        "easy": 4,
                        "medium": 4,
                        "hard": 2
                    },
                    "content_coverage": [1, 2, 3, 4, 5],
                    "status": "ready",
                    "estimated_score_range": "75-90점 예상"
                },
                "message": "이번 주 시험이 생성되었습니다! 지금까지 학습한 내용을 바탕으로 10문제가 준비되었어요."
            }
        
        elif test_type == "start":
            return {
                "success": True,
                "session": {
                    "session_id": f"test_{random.randint(1000, 9999)}",
                    "start_time": datetime.now().isoformat(),
                    "end_time": (datetime.now() + timedelta(minutes=30)).isoformat(),
                    "current_question": 1,
                    "total_questions": 10
                },
                "first_question": {
                    "order": 1,
                    "question": "React에서 컴포넌트 간 데이터 전달을 위해 사용하는 것은?",
                    "type": "multiple_choice",
                    "options": [
                        "Props",
                        "State", 
                        "Context",
                        "Redux"
                    ],
                    "time_limit": 180,
                    "content_title": "React 기초 개념"
                },
                "message": "시험이 시작되었습니다! 화이팅!"
            }

    @staticmethod
    def get_adaptive_test_response(test_type="start", difficulty="medium"):
        """적응형 시험 mock 응답"""
        if test_type == "start":
            return {
                "success": True,
                "test": {
                    "id": random.randint(1, 1000),
                    "type": "adaptive",
                    "initial_difficulty": difficulty,
                    "estimated_duration": 25,
                    "question_pool_size": 50,
                    "adaptive_algorithm": "IRT기반 난이도 조절"
                },
                "first_question": {
                    "id": 1,
                    "question": "다음 중 시간 복잡도가 O(n log n)인 정렬 알고리즘은?",
                    "type": "multiple_choice",
                    "options": [
                        "버블 정렬",
                        "선택 정렬", 
                        "병합 정렬",
                        "삽입 정렬"
                    ],
                    "difficulty": difficulty,
                    "estimated_time": 120
                },
                "message": "적응형 시험이 시작되었습니다. 답변에 따라 난이도가 조절됩니다."
            }

    @staticmethod
    def get_instant_check_response(content_text=""):
        """즉석 콘텐츠 체크 mock 응답"""
        return {
            "success": True,
            "analysis": {
                "comprehension_score": random.randint(75, 95),
                "key_concepts": [
                    "함수형 프로그래밍",
                    "순수 함수",
                    "불변성",
                    "고차 함수"
                ],
                "difficulty_level": "중급",
                "estimated_study_time": random.randint(15, 45),
                "readability_score": random.randint(80, 95)
            },
            "suggestions": {
                "improvements": [
                    "예제 코드를 추가하면 이해가 더 쉬워집니다.",
                    "개념 간의 연관성을 명시해보세요.",
                    "실습 문제를 포함하면 좋겠습니다."
                ],
                "related_topics": [
                    "함수 합성",
                    "모나드 패턴",
                    "커링"
                ],
                "review_schedule": [
                    "1일 후 복습 권장",
                    "3일 후 심화 학습",
                    "7일 후 종합 정리"
                ]
            },
            "generated_questions": [
                {
                    "question": "순수 함수의 특징을 설명하세요.",
                    "type": "short_answer",
                    "difficulty": "easy"
                },
                {
                    "question": "함수형 프로그래밍의 장점은 무엇인가요?",
                    "type": "essay",
                    "difficulty": "medium"
                }
            ]
        }

    @staticmethod
    def get_analytics_response(period_type="weekly"):
        """AI 분석 mock 응답 - LearningAnalytics 인터페이스와 일치"""
        return {
            "id": random.randint(1, 1000),
            "period_type": period_type,
            "period_start": (datetime.now() - timedelta(days=7)).isoformat(),
            "period_end": datetime.now().isoformat(),
            "total_study_minutes": random.randint(180, 420),  # 3-7시간
            "average_daily_minutes": random.randint(25, 60),
            "peak_study_hour": random.randint(9, 21),  # 9-21시
            "study_day_pattern": {
                "mon": random.randint(30, 90),
                "tue": random.randint(20, 80),
                "wed": random.randint(40, 100),
                "thu": random.randint(35, 85),
                "fri": random.randint(25, 75),
                "sat": random.randint(50, 120),
                "sun": random.randint(30, 90)
            },
            "total_contents_studied": random.randint(8, 25),
            "total_reviews_completed": random.randint(15, 45),
            "average_accuracy": round(random.uniform(65, 95), 1),
            "weak_categories": [
                {"category": "알고리즘", "score": random.randint(60, 75)},
                {"category": "데이터베이스", "score": random.randint(65, 80)},
                {"category": "네트워크", "score": random.randint(55, 70)}
            ],
            "strong_categories": [
                {"category": "프론트엔드", "score": random.randint(85, 95)},
                {"category": "백엔드", "score": random.randint(80, 90)},
                {"category": "기초개념", "score": random.randint(88, 98)}
            ],
            "recommended_focus_areas": [
                "알고리즘 기초 개념 재정리가 필요합니다",
                "데이터베이스 쿼리 최적화 학습을 추천합니다",
                "네트워크 프로토콜 이해도를 높이면 좋겠습니다"
            ],
            "personalized_tips": [
                "오전 시간대에 집중도가 높으니 어려운 개념을 이때 학습하세요",
                "짧은 시간이라도 매일 꾸준히 복습하는 것이 효과적입니다",
                "이론 학습 후 바로 실습 문제를 풀어보세요",
                "틀린 문제는 다음 날 다시 한 번 확인해보세요"
            ],
            "predicted_improvement_areas": [
                "알고리즘 정답률 15% 향상 예상",
                "데이터베이스 이해도 개선 기대",
                "전반적 학습 효율성 증대"
            ],
            "efficiency_score": round(random.uniform(75, 95), 1),
            "retention_rate": round(random.uniform(80, 95), 1),
            "created_at": datetime.now().isoformat()
        }

    @staticmethod
    def get_explanation_evaluation_response(user_explanation=""):
        """설명 평가 mock 응답"""
        return {
            "success": True,
            "evaluation": {
                "comprehension_score": random.randint(70, 95),
                "clarity_score": random.randint(65, 90),
                "accuracy_score": random.randint(80, 100),
                "completeness_score": random.randint(75, 95),
                "overall_score": random.randint(75, 92)
            },
            "feedback": {
                "strengths": [
                    "핵심 개념을 정확히 이해하고 있습니다.",
                    "논리적인 순서로 설명을 전개했습니다.",
                    "적절한 예시를 활용했습니다."
                ],
                "improvements": [
                    "더 구체적인 예시를 추가하면 좋겠습니다.",
                    "전문 용어에 대한 정의를 포함해보세요.",
                    "결론 부분을 더 명확하게 정리해주세요."
                ],
                "missing_concepts": [
                    "예외 상황 처리",
                    "성능 고려사항",
                    "실제 사용 사례"
                ]
            },
            "suggested_improvements": {
                "structure": "도입-본론-결론 구조를 더 명확히 하세요.",
                "examples": "실제 코드 예제를 2-3개 더 추가하면 좋겠습니다.",
                "depth": "개념의 '왜'와 '언제'에 대한 설명을 강화하세요."
            },
            "next_steps": [
                "관련된 고급 개념 학습",
                "실습 프로젝트에 적용해보기",
                "다른 사람에게 설명해보기"
            ]
        }