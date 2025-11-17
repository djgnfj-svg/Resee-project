"""
Celery tasks for exam question generation
"""
import logging

from celery import shared_task
from django.db import transaction

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_exam_questions(self, test_id, content_ids=None):
    """
    비동기로 시험 문제 생성

    Args:
        test_id: WeeklyTest ID
        content_ids: 선택된 콘텐츠 ID 리스트 (None이면 자동 밸런싱)
    """
    from ai_services.generators.question_generator import ai_question_generator

    from .models import WeeklyTest

    logger.info(f"[Task] Starting question generation for test {test_id}")

    try:
        weekly_test = WeeklyTest.objects.get(id=test_id)

        # 이미 문제가 생성되어 있으면 스킵
        if weekly_test.questions.exists():
            logger.info(f"[Task] Test {test_id} already has questions, skipping")
            weekly_test.status = 'pending'
            weekly_test.save()
            return

        # AI 사용 가능 여부 확인
        ai_available = ai_question_generator.is_available()

        # content_ids가 있으면 수동 선택, 없으면 자동 밸런싱
        if content_ids:
            _generate_questions_from_ids(weekly_test, content_ids, ai_available)
        else:
            _generate_balanced_questions(weekly_test, ai_available)

        logger.info(f"[Task] Successfully generated {weekly_test.total_questions} questions for test {test_id}")

    except WeeklyTest.DoesNotExist:
        logger.error(f"[Task] Test {test_id} not found")
        raise
    except Exception as e:
        logger.error(f"[Task] Failed to generate questions for test {test_id}: {e}", exc_info=True)

        # 재시도
        try:
            self.retry(countdown=10)
        except Exception:
            # 재시도 실패 시 상태 업데이트
            try:
                weekly_test = WeeklyTest.objects.get(id=test_id)
                weekly_test.status = 'pending'
                weekly_test.save()
            except Exception:
                pass
            raise


def _generate_questions_from_ids(weekly_test, content_ids, ai_available):
    """전달받은 콘텐츠 ID로 순서대로 문제 생성"""
    from content.models import Content

    try:
        with transaction.atomic():
            # 콘텐츠 조회 (AI 검증된 콘텐츠만)
            contents = Content.objects.filter(
                id__in=content_ids,
                author=weekly_test.user,
                is_ai_validated=True
            )

            # 존재하지 않거나 검증되지 않은 콘텐츠가 있으면 에러
            if contents.count() != len(content_ids):
                logger.warning(f"[Task] Some contents not found or not validated")
                return

            # 순서 유지를 위해 딕셔너리 생성 후 재정렬
            content_dict = {c.id: c for c in contents}
            ordered_contents = [content_dict[cid] for cid in content_ids]

            # 각 콘텐츠당 1개 문제 생성 (7-10개)
            for order, content in enumerate(ordered_contents, start=1):
                if ai_available:
                    success = _create_ai_question(weekly_test, content, order)
                    if not success:
                        _create_simple_question(weekly_test, content, order)
                else:
                    _create_simple_question(weekly_test, content, order)

            # 문제 수 업데이트
            weekly_test.total_questions = weekly_test.questions.count()

            # 문제 생성 완료 후 preparing 상태를 pending으로 변경
            if weekly_test.status == 'preparing':
                weekly_test.status = 'pending'

            weekly_test.save()
    except Exception as e:
        logger.error(f"[Task] Failed to generate questions from IDs: {e}", exc_info=True)
        weekly_test.status = 'pending'
        weekly_test.save()
        raise


def _generate_balanced_questions(weekly_test, ai_available):
    """
    난이도 균형 맞춰 자동으로 콘텐츠 선택 및 문제 생성

    LangGraph Balance Graph를 사용하여 30% Easy, 50% Medium, 20% Hard 비율로
    콘텐츠를 자동 선택합니다.
    """
    from ai_services.graphs import select_balanced_contents_for_test
    from content.models import Content

    logger.info(f"[Task] Starting balanced question generation for test {weekly_test.id}")

    # 이미 문제가 생성되어 있으면 스킵
    if weekly_test.questions.exists():
        logger.info(f"[Task] Test {weekly_test.id} already has questions, skipping generation")
        return

    # 사용자의 AI 검증된 콘텐츠 조회
    contents = Content.objects.filter(
        author=weekly_test.user,
        is_ai_validated=True
    ).order_by('-created_at')

    if not contents.exists():
        logger.warning(f"[Task] No AI-validated contents for user {weekly_test.user.id}")
        weekly_test.status = 'pending'
        weekly_test.save()
        return

    # Balance Graph용 데이터 준비
    content_data = [
        {
            'id': content.id,
            'title': content.title,
            'content': content.content
        }
        for content in contents
    ]

    # 목표 문제 수 (7-10개, 콘텐츠 수에 따라 조정)
    target_count = min(10, max(7, len(content_data)))

    logger.info(
        f"[Task] Analyzing {len(content_data)} contents "
        f"for {target_count} balanced questions"
    )

    try:
        # LangGraph Balance Graph 실행
        balance_result = select_balanced_contents_for_test(
            contents=content_data,
            target_count=target_count
        )

        selected_ids = balance_result['selected_content_ids']
        balance_info = balance_result['balance']
        difficulty_scores = balance_result['difficulty_scores']

        logger.info(
            f"[Task] Selected {len(selected_ids)} contents - "
            f"Easy: {balance_info.get('easy', 0)}, "
            f"Medium: {balance_info.get('medium', 0)}, "
            f"Hard: {balance_info.get('hard', 0)}"
        )

        # 선택된 콘텐츠로 문제 생성 (트랜잭션으로 보호)
        with transaction.atomic():
            selected_contents = Content.objects.filter(id__in=selected_ids)
            content_dict = {c.id: c for c in selected_contents}
            ordered_contents = [content_dict[cid] for cid in selected_ids]

            # 각 콘텐츠당 1개 문제 생성
            for order, content in enumerate(ordered_contents, start=1):
                if ai_available:
                    success = _create_ai_question(weekly_test, content, order)
                    if not success:
                        _create_simple_question(weekly_test, content, order)
                else:
                    _create_simple_question(weekly_test, content, order)

            # 밸런스 정보 저장 (메타데이터로)
            weekly_test.total_questions = weekly_test.questions.count()
            weekly_test.metadata = {
                'balance': balance_info,
                'difficulty_scores': {
                    str(cid): score for cid, score in difficulty_scores.items()
                },
                'auto_balanced': True
            }

            # 문제 생성 완료 후 preparing 상태를 pending으로 변경
            if weekly_test.status == 'preparing':
                weekly_test.status = 'pending'

            weekly_test.save()

        logger.info(
            f"[Task] Successfully generated {weekly_test.total_questions} "
            f"balanced questions for test {weekly_test.id}"
        )

    except Exception as e:
        logger.error(
            f"[Task] Failed to generate balanced questions: {e}",
            exc_info=True
        )
        # Fallback: 무작위 선택 (트랜잭션으로 보호)
        with transaction.atomic():
            fallback_contents = list(contents[:target_count])
            for order, content in enumerate(fallback_contents, start=1):
                if ai_available:
                    _create_ai_question(weekly_test, content, order)
                else:
                    _create_simple_question(weekly_test, content, order)

            weekly_test.total_questions = weekly_test.questions.count()
            weekly_test.status = 'pending'
            weekly_test.save()


def _create_ai_question(weekly_test, content, order):
    """
    AI를 사용한 고급 문제 생성

    LangGraph 기반 고품질 Distractor 생성 시스템 사용
    """
    from ai_services.generators.question_generator import ai_question_generator

    from .models import WeeklyTestQuestion

    # 중복 체크: 이미 해당 order에 문제가 있으면 스킵
    if WeeklyTestQuestion.objects.filter(weekly_test=weekly_test, order=order).exists():
        logger.info(f"[Task] Question at order {order} already exists, skipping")
        return True

    try:
        question_data = ai_question_generator.generate_question(content)

        if question_data:
            WeeklyTestQuestion.objects.create(
                weekly_test=weekly_test,
                content=content,
                question_type=question_data['question_type'],
                question_text=question_data['question_text'],
                choices=question_data.get('choices'),
                correct_answer=question_data['correct_answer'],
                explanation=question_data['explanation'],
                order=order,
                points=10
            )
            logger.info(
                f"[Task] AI question generated (quality: "
                f"{question_data.get('metadata', {}).get('quality_score', 0):.1f})"
            )
            return True
        else:
            _create_simple_question(weekly_test, content, order)
            return False

    except Exception as e:
        logger.error(f"[Task] AI generation error: {e}", exc_info=True)
        _create_simple_question(weekly_test, content, order)
        return False


def _create_simple_question(weekly_test, content, order):
    """간단한 문제 생성 (AI 없이) - 개선된 버전"""
    import random

    from .models import WeeklyTestQuestion

    # 중복 체크: 이미 해당 order에 문제가 있으면 스킵
    if WeeklyTestQuestion.objects.filter(weekly_test=weekly_test, order=order).exists():
        logger.info(f"[Task] Question at order {order} already exists, skipping simple question creation")
        return

    # 콘텐츠에서 의미있는 문장 추출
    sentences = _extract_meaningful_sentences(content.content)

    if not sentences:
        # 문장 추출 실패 시 전체 내용 사용
        sentences = [content.content[:200]]

    # 첫 번째 의미있는 문장을 문제로 사용
    selected_sentence = sentences[0] if sentences else content.content[:200]

    # 코드 요소를 백틱으로 감싸기
    selected_sentence = _wrap_code_elements(selected_sentence)

    # O/X 문제 생성 (50% 확률로 O 또는 X)
    is_correct_statement = random.choice([True, False])

    if is_correct_statement:
        # 실제 내용을 그대로 사용 (정답: O)
        question_text = f"'{content.title}'에 대한 다음 설명이 맞습니까? (O/X)\n\n{selected_sentence}"
        correct_answer = "O"
        explanation = f"O - 학습 내용에 정확히 포함된 내용입니다."
    else:
        # 내용을 살짝 변형하여 오답 생성 (정답: X)
        modified_sentence = _create_modified_statement(content.title, selected_sentence)
        modified_sentence = _wrap_code_elements(modified_sentence)
        question_text = f"'{content.title}'에 대한 다음 설명이 맞습니까? (O/X)\n\n{modified_sentence}"
        correct_answer = "X"
        explanation = f"X - 학습 내용과 다릅니다. 정확한 내용: {selected_sentence[:100]}..."

    WeeklyTestQuestion.objects.create(
        weekly_test=weekly_test,
        content=content,
        question_type='true_false',
        question_text=question_text,
        choices=None,
        correct_answer=correct_answer,
        explanation=explanation,
        order=order,
        points=10
    )


def _extract_meaningful_sentences(text):
    """텍스트에서 의미있는 문장 추출"""
    import re

    # 마크다운 헤더, 코드 블록 등 제거
    text = re.sub(r'#+\s+', '', text)  # 헤더 제거
    text = re.sub(r'```.*?```', '', text, flags=re.DOTALL)  # 코드 블록 제거
    text = re.sub(r'`[^`]+`', '', text)  # 인라인 코드 제거

    # 문장 분리 (. ! ? 기준)
    sentences = re.split(r'[.!?]\s+', text)

    # 의미있는 길이의 문장만 필터링 (50-300자)
    meaningful = [s.strip() for s in sentences if 50 <= len(s.strip()) <= 300]

    return meaningful[:3]  # 최대 3개 반환


def _create_modified_statement(title, original_sentence):
    """문장을 살짝 변형하여 오답 생성"""
    import random

    # 간단한 부정 또는 수정을 통해 오답 만들기
    modifications = [
        f"{original_sentence.replace('입니다', '가 아닙니다').replace('합니다', '하지 않습니다')}",
        f"{title}은(는) 다른 개념과 관련이 없습니다.",
        f"{original_sentence[:50]}... 는 잘못된 설명입니다.",
    ]

    return random.choice(modifications)


def _wrap_code_elements(text):
    """코드 요소를 백틱으로 감싸서 마크다운 형식으로 변환"""
    import re

    # 이미 백틱으로 감싸진 부분은 보존
    if '`' in text:
        return text

    # 코드 패턴들 정의
    patterns = [
        # 던더 메서드 (__init__, __str__ 등) - 괄호 포함
        (r'(__[a-zA-Z_]+__)\s*\(', r'`\1`('),
        # 던더 메서드 (__init__, __str__ 등) - 괄호 없음
        (r'(?<![a-zA-Z0-9_])(__[a-zA-Z_]+__)(?![a-zA-Z0-9_])', r'`\1`'),
        # self, cls 같은 특수 키워드 (한글 앞뒤 허용)
        (r'(?<![a-zA-Z0-9_])(self|cls)(?![a-zA-Z0-9_])', r'`\1`'),
        # 함수/메서드 호출 (괄호 포함, 던더 메서드 제외)
        (r'(?<![a-zA-Z0-9_])(?!__)([a-zA-Z_][a-zA-Z0-9_]*)\s*\(', r'`\1`('),
        # 파이썬 키워드들
        (r'(?<![a-zA-Z0-9_])(def|class|import|from|return|if|else|elif|for|while|try|except|with|as|lambda|yield|async|await)(?![a-zA-Z0-9_])', r'`\1`'),
        # 타입 힌트나 타입 이름
        (r'(?<![a-zA-Z0-9_])(int|str|float|bool|list|dict|tuple|set|None|True|False)(?![a-zA-Z0-9_])', r'`\1`'),
        # 변수명 패턴 (언더스코어 포함)
        (r'(?<![a-zA-Z0-9_])([a-z][a-z0-9_]*_[a-z0-9_]+)(?![a-zA-Z0-9_])', r'`\1`'),
    ]

    result = text
    for pattern, replacement in patterns:
        result = re.sub(pattern, replacement, result)

    # 중복 백틱 제거 (예: ``code``)
    result = re.sub(r'`+', '`', result)

    return result
