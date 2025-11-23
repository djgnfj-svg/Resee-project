"""
AI 서비스 패키지

Anthropic Claude를 사용하는 중앙화된 AI 서비스:

검증기 (Validators):
- content_validator: 학습 콘텐츠의 정확성과 일관성을 검증

평가기 (Evaluators):
- ai_answer_evaluator: 사용자의 서술형 답변을 평가
- ai_title_evaluator: 사용자가 추측한 제목을 평가

생성기 (Generators):
- mc_generator: 객관식 보기 생성
- ai_question_generator: 주간 시험 문제 생성 (LangChain + LangGraph)

그래프 (LangGraph 워크플로우):
- generate_quality_choices: 고품질 오답지 생성
- select_balanced_contents_for_test: 균형잡힌 시험 콘텐츠 선택
"""

__version__ = "2.0.0"

from .evaluators import ai_answer_evaluator, ai_title_evaluator
from .generators import (
    ai_question_generator,
    generate_multiple_choice_options,
    mc_generator,
)
from .graphs import (
    create_distractor_generation_graph,
    create_weekly_test_balance_graph,
    generate_quality_choices,
    select_balanced_contents_for_test,
)

# 쉬운 접근을 위해 모든 서비스 import
from .validators import content_validator, validate_content

__all__ = [
    # 검증기
    "content_validator",
    "validate_content",
    # 평가기
    "ai_answer_evaluator",
    "ai_title_evaluator",
    # 생성기
    "mc_generator",
    "generate_multiple_choice_options",
    "ai_question_generator",
    # 그래프
    "generate_quality_choices",
    "select_balanced_contents_for_test",
    "create_distractor_generation_graph",
    "create_weekly_test_balance_graph",
]
