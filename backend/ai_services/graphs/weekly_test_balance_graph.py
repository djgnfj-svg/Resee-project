"""
주간 시험 밸런스 그래프

난이도 분산된 주간 시험 자동 생성
- Easy: 30%
- Medium: 50%
- Hard: 20%
"""

import logging
import random
from typing import Dict, List, TypedDict

from django.conf import settings
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import END, StateGraph

logger = logging.getLogger(__name__)


class WeeklyTestBalanceState(TypedDict):
    """주간 시험 밸런스 상태"""
    contents: List[Dict]  # [{'id': int, 'title': str, 'content': str}]
    target_count: int  # 목표 문제 수 (7-10개)
    difficulty_scores: Dict[int, Dict]  # {content_id: {'difficulty': str, 'score': int}}
    selected_contents: List[int]  # 선택된 content_id 리스트
    balance: Dict[str, int]  # {'easy': n, 'medium': n, 'hard': n}


def analyze_difficulty(state: WeeklyTestBalanceState) -> WeeklyTestBalanceState:
    """
    콘텐츠 난이도 분석

    각 콘텐츠의 난이도를 AI로 평가합니다.
    """
    logger.info(f"[Analyze] Analyzing difficulty for {len(state['contents'])} contents")

    llm = ChatAnthropic(
        model="claude-3-haiku-20240307",
        temperature=0.2,
        max_tokens=200,
        api_key=settings.ANTHROPIC_API_KEY
    )

    prompt = ChatPromptTemplate.from_template("""
다음 학습 콘텐츠의 난이도를 평가하세요.

**콘텐츠**:
제목: {title}
내용: {content}

**난이도 기준**:
- Easy (30-50점): 기본 개념, 단순 정의, 명확한 사실
- Medium (50-70점): 개념 이해, 비교/대조, 적용
- Hard (70-100점): 복잡한 개념, 심화 내용, 응용/분석

**응답 형식** (한 줄로):
difficulty: Easy|Medium|Hard, score: 30-100
""")

    difficulty_scores = {}

    for content_data in state['contents']:
        try:
            response = llm.invoke(prompt.format(
                title=content_data['title'],
                content=content_data['content'][:800]
            ))

            response_text = response.content.strip()

            # 파싱: "difficulty: Medium, score: 65"
            parts = response_text.split(',')
            difficulty = parts[0].split(':')[1].strip()
            score = int(parts[1].split(':')[1].strip())

            difficulty_scores[content_data['id']] = {
                'difficulty': difficulty,
                'score': score
            }

            logger.info(
                f"[Analyze] Content {content_data['id']}: "
                f"{difficulty} (score: {score})"
            )

        except Exception as e:
            logger.error(f"[Analyze] Failed for content {content_data['id']}: {e}")
            # 기본값: Medium
            difficulty_scores[content_data['id']] = {
                'difficulty': 'Medium',
                'score': 60
            }

    state['difficulty_scores'] = difficulty_scores
    logger.info(f"[Analyze] Complete - {len(difficulty_scores)} contents analyzed")

    return state


def select_balanced_contents(state: WeeklyTestBalanceState) -> WeeklyTestBalanceState:
    """
    난이도 균형 맞춰 콘텐츠 선택

    30% Easy, 50% Medium, 20% Hard 비율로 선택
    """
    target_count = state['target_count']
    difficulty_scores = state['difficulty_scores']

    logger.info(f"[Select] Selecting {target_count} contents with 30/50/20 balance")

    # 난이도별로 그룹화
    easy_contents = []
    medium_contents = []
    hard_contents = []

    for content_id, data in difficulty_scores.items():
        difficulty = data['difficulty']
        if difficulty == 'Easy':
            easy_contents.append(content_id)
        elif difficulty == 'Medium':
            medium_contents.append(content_id)
        else:  # Hard
            hard_contents.append(content_id)

    logger.info(
        f"[Select] Available - Easy: {len(easy_contents)}, "
        f"Medium: {len(medium_contents)}, Hard: {len(hard_contents)}"
    )

    # 목표 개수 계산 (30/50/20 비율)
    target_easy = round(target_count * 0.3)
    target_hard = round(target_count * 0.2)
    target_medium = target_count - target_easy - target_hard

    logger.info(
        f"[Select] Target - Easy: {target_easy}, "
        f"Medium: {target_medium}, Hard: {target_hard}"
    )

    # 선택
    selected = []

    # Easy 선택
    if len(easy_contents) >= target_easy:
        selected.extend(random.sample(easy_contents, target_easy))
    else:
        selected.extend(easy_contents)
        logger.warning(f"[Select] Not enough Easy contents ({len(easy_contents)}/{target_easy})")

    # Medium 선택
    remaining_medium_needed = target_medium + (target_easy - len([c for c in selected if c in easy_contents]))
    if len(medium_contents) >= remaining_medium_needed:
        selected.extend(random.sample(medium_contents, remaining_medium_needed))
    else:
        selected.extend(medium_contents)
        logger.warning(f"[Select] Not enough Medium contents ({len(medium_contents)}/{remaining_medium_needed})")

    # Hard 선택
    remaining_hard_needed = target_count - len(selected)
    if len(hard_contents) >= remaining_hard_needed:
        selected.extend(random.sample(hard_contents, remaining_hard_needed))
    else:
        selected.extend(hard_contents)
        logger.warning(f"[Select] Not enough Hard contents ({len(hard_contents)}/{remaining_hard_needed})")

    # 부족하면 남은 것으로 채우기
    if len(selected) < target_count:
        all_content_ids = list(difficulty_scores.keys())
        remaining = [cid for cid in all_content_ids if cid not in selected]
        need = target_count - len(selected)
        if remaining:
            selected.extend(random.sample(remaining, min(need, len(remaining))))

    # 셔플 (난이도 순서 섞기)
    random.shuffle(selected)

    state['selected_contents'] = selected[:target_count]

    # 최종 밸런스 계산
    final_balance = {'easy': 0, 'medium': 0, 'hard': 0}
    for content_id in state['selected_contents']:
        diff = difficulty_scores[content_id]['difficulty'].lower()
        final_balance[diff] = final_balance.get(diff, 0) + 1

    state['balance'] = final_balance

    logger.info(
        f"[Select] Selected {len(state['selected_contents'])} contents - "
        f"Easy: {final_balance['easy']}, "
        f"Medium: {final_balance['medium']}, "
        f"Hard: {final_balance['hard']}"
    )

    return state


def create_weekly_test_balance_graph() -> StateGraph:
    """주간 시험 밸런스 그래프 생성"""

    workflow = StateGraph(WeeklyTestBalanceState)

    # 노드 추가
    workflow.add_node("analyze", analyze_difficulty)
    workflow.add_node("select", select_balanced_contents)

    # 엣지 설정
    workflow.set_entry_point("analyze")
    workflow.add_edge("analyze", "select")
    workflow.add_edge("select", END)

    return workflow.compile()


def select_balanced_contents_for_test(
    contents: List[Dict],
    target_count: int = 10
) -> Dict:
    """
    난이도 균형 맞춰 콘텐츠 선택

    Args:
        contents: [{'id': int, 'title': str, 'content': str}, ...]
        target_count: 목표 문제 수 (기본 10개)

    Returns:
        {
            'selected_content_ids': [id1, id2, ...],
            'balance': {'easy': n, 'medium': n, 'hard': n},
            'difficulty_scores': {id: {'difficulty': str, 'score': int}}
        }
    """
    logger.info(f"[Graph] Creating balance graph for {len(contents)} contents")

    if len(contents) < target_count:
        logger.warning(
            f"[Graph] Not enough contents ({len(contents)} < {target_count}), "
            f"using all available"
        )
        target_count = len(contents)

    graph = create_weekly_test_balance_graph()

    initial_state: WeeklyTestBalanceState = {
        'contents': contents,
        'target_count': target_count,
        'difficulty_scores': {},
        'selected_contents': [],
        'balance': {}
    }

    result = graph.invoke(initial_state)

    logger.info(
        f"[Graph] Complete - Selected {len(result['selected_contents'])} contents "
        f"(Balance: {result['balance']})"
    )

    return {
        'selected_content_ids': result['selected_contents'],
        'balance': result['balance'],
        'difficulty_scores': result['difficulty_scores']
    }
