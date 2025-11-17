"""
Distractor Generation Graph - 고품질 객관식 오답 생성

교육학적으로 의미 있는 오답(Distractor)을 생성하여
학습자의 진정한 이해도를 평가합니다.

핵심 전략:
    - Type A: 반대 개념 혼동 (70-85점 그럴듯함)
    - Type B: 부분적 이해 (60-75점, 가장 헷갈림)
    - Type C: 유사 개념 혼동 (65-80점)

Graph Flow:
    START → Extract Concepts → Generate Distractors → Validate Quality
    → [Quality ≥ 80?] → Improve (1회) or Finalize → END
"""

import json
import logging
import random
from typing import Dict, List, Literal, Optional, TypedDict

from django.conf import settings
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph

logger = logging.getLogger(__name__)


# ========== State Definition ==========

class DistractorGenerationState(TypedDict):
    """Distractor 생성 프로세스의 상태"""
    # 입력
    content_title: str
    content_body: str
    correct_answer: str
    iteration: int

    # Step 1: Concept Extraction
    core_concepts: List[str]
    misconceptions: List[Dict[str, str]]
    similar_concepts: List[str]

    # Step 2: Distractor Generation
    distractors: List[Dict[str, any]]

    # Step 3: Validation
    validation_result: Dict[str, any]
    quality_score: float
    quality_issues: List[str]

    # Final
    final_choices: List[str]
    metadata: Dict[str, any]


# ========== Helper Functions ==========

def _parse_json_response(response_text: str) -> Optional[Dict]:
    """JSON 응답 파싱 (코드 블록 제거 포함)"""
    try:
        text = response_text.strip()

        # 코드 블록 제거
        if text.startswith('```json'):
            text = text[7:-3].strip()
        elif text.startswith('```'):
            text = text[3:-3].strip()

        return json.loads(text)

    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing failed: {e}")
        logger.debug(f"Raw response: {response_text[:300]}...")
        return None
    except Exception as e:
        logger.error(f"Response parsing error: {e}")
        return None


def _get_llm(temperature: float = 0.3, max_tokens: int = 1000) -> ChatAnthropic:
    """LLM 인스턴스 생성"""
    api_key = getattr(settings, 'ANTHROPIC_API_KEY', None)

    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    return ChatAnthropic(
        model="claude-3-haiku-20240307",
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=api_key
    )


# ========== Node Functions ==========

def extract_concepts_and_misconceptions(
    state: DistractorGenerationState
) -> DistractorGenerationState:
    """
    Step 1: 핵심 개념 및 오개념 추출

    정답을 분석하여 교육학적으로 의미 있는 오개념을 도출합니다.
    """
    logger.info(f"[Extract] Analyzing: {state['content_title']}")

    llm = _get_llm(temperature=0.3, max_tokens=800)

    prompt = ChatPromptTemplate.from_template("""
다음 학습 콘텐츠와 정답을 분석하여 핵심 개념과 흔한 오개념을 추출하세요.

**콘텐츠 정보:**
제목: {title}
내용 (일부): {content}

**정답:**
{correct_answer}

**추출 항목:**

1. **핵심 개념 (Core Concepts)**: 1-2개
   정답에서 가장 중요한 개념
   예: ["mutable", "수정 가능성"]

2. **흔한 오개념 (Common Misconceptions)**: 3가지 유형

   **Type A - 반대 개념 혼동:**
   학습자가 핵심 개념을 정반대로 이해하는 경우
   예: "mutable과 immutable을 반대로 이해"

   **Type B - 부분적 이해:**
   개념은 알지만 적용을 제한적으로 이해하는 경우
   예: "mutable은 알지만 길이 변경은 안 된다고 생각"

   **Type C - 유사 개념 혼동:**
   관련된 다른 개념의 특성과 혼동하는 경우
   예: "튜플의 immutable 특성을 리스트에 적용"

3. **유사 개념 (Similar Concepts)**: 2-3개
   정답과 관련되어 혼동하기 쉬운 개념들
   예: ["tuple", "string", "immutable"]

**응답 형식 (JSON만, 다른 텍스트 없이):**
{{
  "core_concepts": ["개념1", "개념2"],
  "misconceptions": [
    {{
      "type": "A",
      "name": "반대 개념 혼동",
      "description": "구체적인 오개념 설명",
      "example_error": "학습자가 가질 수 있는 오해"
    }},
    {{
      "type": "B",
      "name": "부분적 이해",
      "description": "구체적인 오개념 설명",
      "example_error": "학습자가 가질 수 있는 오해"
    }},
    {{
      "type": "C",
      "name": "유사 개념 혼동",
      "description": "구체적인 오개념 설명",
      "example_error": "학습자가 가질 수 있는 오해"
    }}
  ],
  "similar_concepts": ["개념1", "개념2", "개념3"]
}}
""")

    try:
        response = llm.invoke(prompt.format(
            title=state['content_title'],
            content=state['content_body'][:1500],
            correct_answer=state['correct_answer']
        ))

        result = _parse_json_response(response.content)

        if result:
            state['core_concepts'] = result.get('core_concepts', [])
            state['misconceptions'] = result.get('misconceptions', [])
            state['similar_concepts'] = result.get('similar_concepts', [])

            logger.info(
                f"[Extract] Success - {len(state['misconceptions'])} misconceptions"
            )
        else:
            logger.warning("[Extract] Failed to parse response, using defaults")
            state['core_concepts'] = []
            state['misconceptions'] = []
            state['similar_concepts'] = []

    except Exception as e:
        logger.error(f"[Extract] Error: {e}", exc_info=True)
        state['core_concepts'] = []
        state['misconceptions'] = []
        state['similar_concepts'] = []

    return state


def generate_typed_distractors(
    state: DistractorGenerationState
) -> DistractorGenerationState:
    """
    Step 2: 유형별 Distractor 생성 (★핵심★)

    교육학적 오개념을 반영한 3가지 유형의 그럴듯한 오답을 생성합니다.
    """
    is_improvement = state['iteration'] > 0
    mode = "Improve" if is_improvement else "Generate"

    logger.info(f"[{mode}] Iteration {state['iteration']}")

    llm = _get_llm(temperature=0.3, max_tokens=1200)

    if is_improvement:
        # 개선 모드
        prompt = ChatPromptTemplate.from_template("""
이전 오답의 문제점을 개선하여 재생성하세요.

**정답:**
{correct_answer}

**이전 오답들:**
{previous_distractors}

**문제점:**
{quality_issues}

**개선 원칙:**
1. 길이 균형: 정답 길이({correct_len}자)의 80-120% 범위
2. 그럴듯함 향상: 명확히 틀렸지만 고민하게 만들기
3. 오개념 명확화: 각 오답이 특정 오개념 반영

**응답 형식 (JSON만):**
{{
  "distractors": [
    {{
      "type": "A",
      "text": "개선된 Type A 오답",
      "misconception": "반영한 오개념",
      "plausibility_score": 70-85
    }},
    {{
      "type": "B",
      "text": "개선된 Type B 오답",
      "misconception": "반영한 오개념",
      "plausibility_score": 60-75
    }},
    {{
      "type": "C",
      "text": "개선된 Type C 오답",
      "misconception": "반영한 오개념",
      "plausibility_score": 65-80
    }}
  ]
}}
""")

        response = llm.invoke(prompt.format(
            correct_answer=state['correct_answer'],
            previous_distractors=json.dumps(
                state['distractors'], ensure_ascii=False, indent=2
            ),
            quality_issues='\n'.join(f"- {issue}" for issue in state['quality_issues']),
            correct_len=len(state['correct_answer'])
        ))

    else:
        # 초기 생성 모드
        misconceptions = state['misconceptions']

        # 오개념이 부족한 경우 기본값 사용
        if len(misconceptions) < 3:
            logger.warning("[Generate] Insufficient misconceptions, using defaults")
            misconceptions = [
                {"type": "A", "description": "반대 개념 혼동"},
                {"type": "B", "description": "부분적 이해"},
                {"type": "C", "description": "유사 개념 혼동"}
            ]

        prompt = ChatPromptTemplate.from_template("""
다음 정답에 대해 교육학적으로 의미 있는 오답 3개를 생성하세요.

**정답:**
"{correct_answer}" (길이: {correct_len}자)

**핵심 개념:** {core_concepts}
**오개념 분석:** {misconceptions}
**유사 개념:** {similar_concepts}

**3가지 유형의 오답 생성:**

**Type A - 반대 개념 혼동 (Opposite Concept)**
오개념: {misconception_a}
생성 전략:
- 핵심 개념을 정반대로 뒤집기
- 정답과 같은 문법 구조 유지
- 명확히 틀렸지만 그럴듯함 (70-85점)

**Type B - 부분적 이해 (Partial Understanding)**
오개념: {misconception_b}
생성 전략:
- 절반은 맞고 절반은 틀리게
- 용어는 맞지만 의미를 제한적으로 표현
- 가장 헷갈려야 함 (60-75점)

**Type C - 유사 개념 혼동 (Similar Concept Confusion)**
오개념: {misconception_c}
생성 전략:
- 관련된 다른 개념의 특성을 섞어서
- {similar_concepts} 중 하나를 활용
- 관련성 있지만 틀림 (65-80점)

**제약 조건:**
1. 각 오답 길이: {min_len}-{max_len}자 (정답의 ±20%)
2. 문법적으로 자연스러움
3. "모두 맞다", "없다" 같은 메타 선택지 금지
4. 각 오답이 서로 다른 오개념 반영

**응답 형식 (JSON만, 다른 텍스트 없이):**
{{
  "distractors": [
    {{
      "type": "A",
      "text": "Type A 오답 내용 (정답 길이의 80-120%)",
      "misconception": "반영한 오개념",
      "plausibility_score": 70-85
    }},
    {{
      "type": "B",
      "text": "Type B 오답 내용",
      "misconception": "반영한 오개념",
      "plausibility_score": 60-75
    }},
    {{
      "type": "C",
      "text": "Type C 오답 내용",
      "misconception": "반영한 오개념",
      "plausibility_score": 65-80
    }}
  ]
}}
""")

        correct_len = len(state['correct_answer'])
        min_len = int(correct_len * 0.8)
        max_len = int(correct_len * 1.2)

        response = llm.invoke(prompt.format(
            correct_answer=state['correct_answer'],
            correct_len=correct_len,
            min_len=min_len,
            max_len=max_len,
            core_concepts=json.dumps(state['core_concepts'], ensure_ascii=False),
            misconceptions=json.dumps(misconceptions, ensure_ascii=False, indent=2),
            similar_concepts=', '.join(state['similar_concepts']),
            misconception_a=misconceptions[0].get('description', '반대 개념'),
            misconception_b=misconceptions[1].get('description', '부분적 이해'),
            misconception_c=misconceptions[2].get('description', '유사 개념')
        ))

    # JSON 파싱
    try:
        result = _parse_json_response(response.content)

        if result and 'distractors' in result:
            state['distractors'] = result['distractors']
            logger.info(f"[{mode}] Success - {len(state['distractors'])} distractors")
        else:
            logger.warning(f"[{mode}] Failed to parse, keeping previous")
            if not state.get('distractors'):
                state['distractors'] = []

    except Exception as e:
        logger.error(f"[{mode}] Error: {e}", exc_info=True)
        if not state.get('distractors'):
            state['distractors'] = []

    return state


def validate_choices_quality(
    state: DistractorGenerationState
) -> DistractorGenerationState:
    """
    Step 3: 선택지 품질 검증

    5가지 기준으로 엄격하게 품질을 평가합니다.
    """
    logger.info("[Validate] Checking quality")

    # 오답이 3개 미만이면 품질 0점
    if len(state.get('distractors', [])) < 3:
        logger.warning("[Validate] Insufficient distractors (< 3)")
        state['validation_result'] = {}
        state['quality_score'] = 0.0
        state['quality_issues'] = ["오답 개수 부족 (3개 미만)"]
        return state

    llm = _get_llm(temperature=0.3, max_tokens=900)

    # 모든 선택지
    all_choices = [state['correct_answer']] + [
        d['text'] for d in state['distractors'][:3]
    ]
    lengths = [len(c) for c in all_choices]

    prompt = ChatPromptTemplate.from_template("""
다음 객관식 선택지의 품질을 엄격하게 평가하세요.

**정답:** {correct_answer}

**전체 선택지:**
{all_choices}

**Distractor 정보:**
{distractors}

**평가 기준:**

**1. Plausibility (그럴듯함) - 30%**
각 Distractor가 목표 범위 내인가?
- Type A: 70-85점 (명확히 틀렸지만 그럴듯)
- Type B: 60-75점 (가장 헷갈림)
- Type C: 65-80점 (관련성 있지만 틀림)

**2. Length Balance (길이 균형) - 20%**
정답: {correct_len}자
각 선택지: {lengths}

- 각 선택지가 정답의 80-120% 범위?
- 길이로 정답 예측 불가능?

**3. Grammar & Naturalness (문법/자연스러움) - 20%**
모든 선택지가:
- 문법 오류 없음?
- 자연스러운 문장?

**4. Misconception Coverage (오개념 반영) - 20%**
각 Distractor가:
- 명확한 오개념 반영?
- 3개가 서로 다른 오개념?

**5. Discrimination (변별력) - 10%**
- 정답이 너무 명확하지 않은가?
- 학습자가 고민하게 만드는가?

**응답 형식 (JSON만):**
{{
  "plausibility": {{
    "score": 0-100,
    "issues": ["문제점1", ...]
  }},
  "length_balance": {{
    "score": 0-100,
    "issues": ["문제점1", ...]
  }},
  "grammar": {{
    "score": 0-100,
    "issues": []
  }},
  "misconception_coverage": {{
    "score": 0-100,
    "issues": ["문제점1", ...]
  }},
  "discrimination": {{
    "score": 0-100,
    "issues": []
  }},
  "overall_score": 종합 점수 (가중 평균),
  "summary_issues": ["주요 문제점1", "주요 문제점2"]
}}

엄격하게 평가하세요. 80점 이상은 정말 우수한 경우에만 부여하세요.
""")

    try:
        response = llm.invoke(prompt.format(
            correct_answer=state['correct_answer'],
            all_choices=json.dumps(all_choices, ensure_ascii=False, indent=2),
            distractors=json.dumps(
                state['distractors'][:3], ensure_ascii=False, indent=2
            ),
            correct_len=len(state['correct_answer']),
            lengths=lengths
        ))

        result = _parse_json_response(response.content)

        if result:
            state['validation_result'] = result
            state['quality_score'] = float(result.get('overall_score', 0))
            state['quality_issues'] = result.get('summary_issues', [])

            logger.info(f"[Validate] Quality score: {state['quality_score']:.1f}")
        else:
            logger.warning("[Validate] Failed to parse, using default")
            state['validation_result'] = {}
            state['quality_score'] = 0.0
            state['quality_issues'] = ["검증 응답 파싱 실패"]

    except Exception as e:
        logger.error(f"[Validate] Error: {e}", exc_info=True)
        state['validation_result'] = {}
        state['quality_score'] = 0.0
        state['quality_issues'] = [f"검증 오류: {str(e)}"]

    return state


def finalize_choices(
    state: DistractorGenerationState
) -> DistractorGenerationState:
    """
    Step 4: 최종화

    정답 + 오답 3개를 섞어서 최종 선택지를 구성합니다.
    """
    logger.info(f"[Finalize] Quality: {state['quality_score']:.1f}")

    # 정답 + 오답 3개
    choices = [state['correct_answer']] + [
        d['text'] for d in state['distractors'][:3]
    ]

    # 랜덤 섞기 (정답 위치 랜덤화)
    random.shuffle(choices)

    state['final_choices'] = choices

    # 메타데이터
    state['metadata'] = {
        'quality_score': state['quality_score'],
        'iterations': state['iteration'],
        'validation_details': state['validation_result'],
        'correct_answer': state['correct_answer'],
        'distractors_info': state['distractors'][:3]
    }

    logger.info(f"[Finalize] Complete after {state['iteration']} iterations")

    return state


# ========== Conditional Edge ==========

def should_improve(
    state: DistractorGenerationState
) -> Literal["improve", "finalize"]:
    """
    품질 기준에 따라 개선 여부 결정

    - quality_score >= 80: 충분히 좋음 → 완료
    - iteration >= 1: 최대 1회 개선만 → 완료
    - 그 외: 개선 필요 → 재생성
    """
    quality_score = state['quality_score']
    iteration = state['iteration']

    if quality_score >= 80:
        logger.info(f"[Decision] Quality sufficient ({quality_score:.1f}) → Finalize")
        return "finalize"

    if iteration >= 1:
        logger.warning(f"[Decision] Max iteration reached → Finalize anyway")
        return "finalize"

    logger.info(f"[Decision] Quality low ({quality_score:.1f}) → Improve")
    return "improve"


def increment_iteration(
    state: DistractorGenerationState
) -> DistractorGenerationState:
    """반복 횟수 증가"""
    state['iteration'] += 1
    logger.info(f"[Loop] Starting iteration {state['iteration']}")
    return state


# ========== Graph Construction ==========

def create_distractor_generation_graph():
    """
    Distractor 생성 그래프 생성

    Returns:
        Compiled StateGraph
    """
    workflow = StateGraph(DistractorGenerationState)

    # Nodes
    workflow.add_node("extract", extract_concepts_and_misconceptions)
    workflow.add_node("generate", generate_typed_distractors)
    workflow.add_node("validate", validate_choices_quality)
    workflow.add_node("increment", increment_iteration)
    workflow.add_node("finalize", finalize_choices)

    # Flow
    workflow.set_entry_point("extract")
    workflow.add_edge("extract", "generate")
    workflow.add_edge("generate", "validate")

    # Conditional routing
    workflow.add_conditional_edges(
        "validate",
        should_improve,
        {
            "improve": "increment",
            "finalize": "finalize"
        }
    )

    workflow.add_edge("increment", "generate")
    workflow.add_edge("finalize", END)

    # Compile
    app = workflow.compile()

    logger.info("[Graph] Distractor generation graph compiled")

    return app


# ========== Main Function ==========

def generate_quality_choices(
    content_title: str,
    content_body: str,
    correct_answer: str
) -> Dict[str, any]:
    """
    고품질 객관식 보기 생성 (메인 함수)

    Args:
        content_title: 콘텐츠 제목
        content_body: 콘텐츠 내용
        correct_answer: 정답

    Returns:
        {
            'choices': [...],  # 섞인 선택지 4개
            'correct_answer': "정답",
            'metadata': {...}  # 품질 정보
        }
    """
    graph = create_distractor_generation_graph()

    initial_state = {
        "content_title": content_title,
        "content_body": content_body,
        "correct_answer": correct_answer,
        "iteration": 0,
        "core_concepts": [],
        "misconceptions": [],
        "similar_concepts": [],
        "distractors": [],
        "validation_result": {},
        "quality_score": 0.0,
        "quality_issues": [],
        "final_choices": [],
        "metadata": {}
    }

    try:
        result = graph.invoke(initial_state)

        return {
            'choices': result['final_choices'],
            'correct_answer': result['correct_answer'],
            'metadata': result['metadata']
        }

    except Exception as e:
        logger.error(f"[Error] Graph execution failed: {e}", exc_info=True)
        return {
            'choices': [],
            'correct_answer': correct_answer,
            'metadata': {'error': str(e)}
        }
